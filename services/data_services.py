import logging
import glob
import os
import re
import sqlite3
import tempfile

from itertools import islice

import pandas as pd
import plotly.express as px

logger = logging.getLogger('cli')


class DataServices:
    CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F"]')
    data_columns = ['wall_time',
                    'fuel_quanty',
                    'rpm_left',
                    'rpm_right',
                    'rpm',
                    'mp',
                    'temp_comp',
                    'volts',
                    'volts_ann',
                    'amps',
                    'fuel_flow',
                    'egt1',
                    'egt2',
                    'egt3',
                    'egt4',
                    'egt5',
                    'egt6',
                    'egt',
                    'egt_d',
                    'egt_h',
                    'cht1',
                    'cht2',
                    'cht3',
                    'cht4',
                    'cht5',
                    'cht6',
                    'cht',
                    'cht_d',
                    'cht_h',
                    'fuel_pressure',
                    'fuel_pressure_ann',
                    'udp',
                    'oil_press',
                    'oil_press_ann',
                    'oil_temp',
                    'oil_temp_ann',
                    'turbo_inlet_t',
                    'hp',
                    'flight_hours',
                    'estimated_total_fuel',
                    'range',
                    'dist_to_dest',
                    'dist_at_dest',
                    'fuel_remain',
                    'fuel_to_dest',
                    'fuel_at_dest',
                    'time_to_empty',
                    'time_to_dest',
                    'time_at_dest',
                    'distance',
                    'flight_time',
                    'fuel_quantity',
                    'flight_fuel',
                    'fuel_since_add',
                    'fuel_economy',
                    'fuel_engine',
                    'tank_switch_in',
                    'tank_switch_ann',
                    'fuel_ann',
                    'gps_altitude',
                    'ground_speed',
                    'waypoint',
                    'distance_to_waypoint',
                    'distance_to_dest',
                    'latitude',
                    'longitude']

    def load_csvs(self, path):
        logger.debug(f'Loading csvs from path {path}')

        csv_path = f'{path}{os.sep}*.csv'
        files = glob.glob(pathname=csv_path)

        for f in files:
            self.load_csv(path=f)

    def load_csv(self, path):
        # first utf-8 encode these..and remove any corrupted data.
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=True) as f_out:
            with open(path, "rb") as f_in:
                logger.info(f'Processing file: {path}')
                text = f_in.read().decode("utf-8", errors="ignore")
                text = self.CONTROL_CHARS.sub('', text)  # strip control chars
                f_out.write(text)
                f_out.flush()  # make sure all data is written

            flight_status = self._get_flight_status(path)

            # Seek back to start so you can read it
            f_out.seek(0)
            head = list(islice(f_out, 14))
            head_row = [(self._find_header_value(head, 'Tracking Number'),
                         self._find_header_value(head,'Local Time'),
                         self._find_header_value(head,'Zulu Time'),
                         self._find_header_value(head,'Flight Number'),
                         self._find_header_value(head,'Engine Hours'),
                         self._find_header_value(head,'Tach Time'),
                         self._get_flight_status(file_name=path))]
            flight_df = pd.DataFrame(head_row,
                                     columns=['tracking_number', 'local_time', 'zulu_time', 'flight_number', 'hobbs',
                                              'tach','flight_status'])

            f_out.seek(0)
            flight_data = pd.read_csv(f_out, skiprows=14)
            flight_data.columns = self.data_columns
            flight_data['flight_number'] = int(flight_df['flight_number'])
            flight_data['tracking_number'] = int(flight_df['tracking_number'])
            flight_data['flight_status'] = flight_df['flight_status'].iloc[0]

            base_date_str = pd.to_datetime(flight_df['local_time'].iloc[0], format='%Y/%m/%d %H:%M:%S').strftime('%m-%d-%Y')
            flight_data['timestamp'] = flight_data['wall_time'].apply(
                lambda t: pd.to_datetime(f"{base_date_str} {t}", format='%m-%d-%Y %H:%M:%S')
            )

            # Connect to (or create) SQLite database file
            conn = sqlite3.connect('./n38701.db')

            logger.info(f'Writing FLIGHT to flights.')
            flight_df.to_sql('flights', conn, if_exists='append', index=False)

            logger.info(f'Writing FLIGHT DATA to flight_data. nrows={len(flight_data)}')
            flight_data.to_sql('flight_data', conn, if_exists='append', index=False)

            # Close the connection
            conn.close()

    def analyze_error(self, error_code='A2D',flight_status='flight',database='./n38701.db'):
        conn = sqlite3.connect(database)
        logger.info(f'Analyzing error {error_code}')
        # Example DataFrame
        logger.debug(f'Reading error code {error_code} for flight status {flight_status} from db {database}')
        sql = f"select * from flight_data where flight_status = '{flight_status}'"
        df = pd.read_sql(sql=sql, con=conn)

        # Identify where "a2d" appears and reshape to long form
        logger.debug('Reshaping data.')
        mask = df.set_index('timestamp') == error_code
        long_df = mask.reset_index().melt(id_vars='timestamp', var_name='Column', value_name=f'is_{error_code}')

        # Filter to only error_code occurrences
        long_df = long_df[long_df[f'is_{error_code}']]

        # Create interactive scatter plot
        logger.debug('Creating plot.')
        fig = px.scatter(
            long_df,
            x='timestamp',
            y='Column',
            color_discrete_sequence=['red'],
            title=f'Occurrences of {error_code} Over Time',
            labels={'timestamp': 'Time', 'Column': 'Column Name'},
            hover_data={'timestamp': True, 'Column': True}
        )

        fig.update_traces(marker=dict(size=10))
        fig.update_layout(yaxis=dict(autorange='reversed'))  # optional: match heatmap style

        logger.info(f'Launching view for "Occurrences of {error_code} Over Time"')
        fig.show()

    def _find_header_value(self, header, label):
        match = next((item for item in header if item.startswith(label)), None)
        if match is not None:
            out = match.split(':')[1].strip().replace(' hrs','')

            if label in ['Local Time', 'Zulu Time']:
                out = ':'.join(match.split(':')[1:]).strip()

            return out
        else:
            raise ValueError(f'Cannot find {label} in header.')

    def _get_flight_status(self, file_name):
        # Mapping
        code_map = {
            'F': 'flight',
            'E': 'engine_on_only',
            'P': 'power_on_only'
        }

        # Regex to capture the letter before .csv
        pattern = re.compile(r'([FEP])\.csv$', re.IGNORECASE)

        match = pattern.search(file_name)
        if match:
            code = match.group(1).upper()
            return code_map.get(code, 'unknown')

        return "unknown"

