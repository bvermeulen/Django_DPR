import matplotlib.dates as mdates

# common variables for seismicreport

# this is for contract c3100000120, effective Jan-2021
TCF_table = {
    'sp_t1': 0.85,
    'sp_t2': 0.60,
    'sp_t3': 0.55,
    'sp_t4': 0.60,
    'sp_t5': 0.60,
}

BGP_DR_table = {
    'date': (0, 1),
    'seq_report': (1, 1),
    'crew': (2, 1),
    'project': (3, 1),
    'block': (3, 5),
    'source_a': (4, 1),
    'sp_t1_a': (6, 1),
    'sp_t2_a': (7, 1),
    'sp_t3_a': (8, 1),
    'sp_t4_a': (9, 1),
    'sp_t5_a': (10, 1),
    'skips_a': (12, 1),
    'source_b': (4, 3),
    'sp_t1_b': (6, 3),
    'sp_t2_b': (7, 3),
    'sp_t3_b': (8, 3),
    'sp_t4_b': (9, 3),
    'sp_t5_b': (10, 3),
    'skips_b': (12, 3),
    'source_c': (4, 5),
    'sp_t1_c': (6, 5),
    'sp_t2_c': (7, 5),
    'sp_t3_c': (8, 5),
    'sp_t4_c': (9, 5),
    'sp_t5_c': (10, 5),
    'skips_c': (12, 5),
    'tcf': (13, 1),
    'rec hours': (25, 1),
    'rec moveup': (26, 1),
    'logistics': (27, 1),
    'wait source': (29, 1),
    'wait layout': (30, 1),
    'wait shift change': (31, 1),
    'company suspension': (33, 1),
    'company tests': (34, 1),
    'beyond contractor control': (35, 1),
    'camp move': (36, 1),
    'line fault': (100, 1), # not used
    'Rec. eqpmt fault': (38, 1),
    'vibrator fault': (39, 1),
    'incident': (40, 1),
    'Legal/ dispute': (41, 1),
    'DT comp. instruction': (42, 1),
    'Contractor noise': (43, 1),
    'other dt': (44, 1),
    'layout': (47, 11),
    'pickup': (48, 11),
    'node download': (40, 11),
    'node charged': (41, 11),
    'node failure': (42, 11),
    'node repair': (43, 11),
    'node qc': (44, 11),
    'comment 1': (0, 10),
    'comment 2': (1, 10),
    'comment 3': (2, 10),
    'comment 4': (3, 10),
    'comment 5': (4, 10),
    'comment 6': (5, 10),
    'comment 7': (6, 10),
    'toolbox 1': (8, 10),
    'toolbox 2': (9, 10),
    'toolbox 3': (10, 10),
    'toolbox 4': (11, 10),
    'toolbox 5': (8, 12),
    'toolbox 6': (9, 12),
    'toolbox 7': (10, 12),
    'toolbox 8': (11, 12),
    'weather condition': (14, 10),
    'rain': (14, 12),
    'temp max': (14, 13),
    'temp min': (14, 14),
    'qc': (31, 10),
    'data qc': (31, 11),
    'geometry qc': (31, 12),
    'data shipped': (31, 14),
    'hse stop cards': (34, 11),
    'hse lti': (35, 11),
    'hse fac': (36, 11),
    'hse mtc': (37, 11),
    'hse RWC': (38, 11),
    'hse incident or nm': (34, 14),
    'hse medevac': (35, 14),
    'hse drills': (36, 14),
    'hse audits': (37, 14),
    'hse lsr violation': (38, 14),
    'headcount': (47, 9),
    'exposure hours': (48, 9),
}

source_prod_schema = [
    'sp_t1_flat', 'sp_t2_rough', 'sp_t3_facilities', 'sp_t4_dunes',
    'sp_t5_sabkha', 'skips',
]

receiver_prod_schema = [
    'layout', 'pickup', 'node_download', 'node_charged', 'node_failure', 'node_repair',
    'qc_field',
]

time_breakdown_schema = [
    'rec_hours', 'rec_moveup', 'logistics', 'camp_move', 'wait_source', 'wait_layout',
    'wait_shift_change', 'company_suspension', 'company_tests', 'beyond_control',
    'line_fault', 'rec_eqpmt_fault', 'vibrator_fault', 'incident', 'legal_dispute',
    'comp_instruction', 'contractor_noise', 'other_downtime',
]

ops_time_keys = [
    'rec_hours', 'rec_moveup', 'logistics', 'wait_source', 'wait_layout',
    'wait_shift_change',
]

standby_keys = ['company_suspension', 'company_tests', 'beyond_control', 'camp_move']

downtime_keys = [
    'line_fault', 'rec_eqpmt_fault', 'vibrator_fault', 'incident', 'legal_dispute',
    'comp_instruction', 'contractor_noise', 'other_downtime',
]

hse_weather_schema = [
    'stop', 'lti', 'fac', 'mtc', 'rwc', 'incident_nm', 'medevac', 'drills', 'audits',
    'lsr_violations', 'headcount', 'exposure_hours', 'weather_condition', 'rain',
    'temp_min', 'temp_max',
]

CTM_METHOD = 'Legacy'
CONTRACT = 'c3100000120'
WEEKDAYS = 7
WEEKS = 6
AVG_PERIOD = 14
STOP_TARGET = (9, 9)
PROD_TARGET = (0.8, 0.9)
REC_TARGET = (21, 23)
NO_DATE_STR = '-'
RIGHT_ARROW = '\u25B6'
LEFT_ARROW = '\u25C0'
SS_2 = '\u00B2'  # superscript 2 for like km2
IMG_SIZE = (310, 248)
NAME_LENGTH = 20
DESCR_LENGTH = 100
TYPE_LENGTH = 10
COMMENT_LENGTH = 5000
WIDGET_WIDTH_PROJECT_FIELDS = 'width:100px'
TICK_SPACING_PROD = 5      # x 1000
TICK_SPACING_CUMUL = 500   # x 1000
TICK_DATE_FORMAT = mdates.DateFormatter('%d-%b-%y')
