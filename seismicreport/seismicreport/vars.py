# common variables for seismicreport

TCF_table = {
    'flat': 0.85,
    'rough': 0.50,
    'facilities': 0.55,
    'dunes': 0.60,
    'sabkha': 0.6,
}

SOURCETYPE_NAME = 'vibe_25m'
RECEIVERTYPE_NAME = 'receiver_25m'

BGP_DR_table = {
    'date': (0, 1),
    'seq_report': (1, 1),
    'crew': (2, 1),
    'project': (3, 1),
    'block': (3, 2),
    'sp_t1': (5, 1),
    'sp_t2': (6, 1),
    'sp_t3': (7, 1),
    'sp_t4': (8, 1),
    'sp_t5': (9, 1),
    'tcf': (11, 1),
    'skips': (12, 1),
    'rec hours': (24, 1),
    'rec moveup': (25, 1),
    'logistics': (26, 1),
    'wait source': (28, 1),
    'wait layout': (29, 1),
    'wait shift change': (30, 1),
    'company suspension': (32, 1),
    'company tests': (33, 1),
    'beyond contractor control': (34, 1),
    'camp move': (35, 1),
    'line fault': (37, 1),
    'instrument fault': (38, 1),
    'vibrator fault': (39, 1),
    'incident': (40, 1),
    'holiday': (41, 1),
    'recovering': (42, 1),
    'other dt': (43, 1),
    'layout': (46, 5),
    'pickup': (47, 5),
    'comment 1': (0, 4),
    'comment 2': (1, 4),
    'comment 3': (2, 4),
    'comment 4': (3, 4),
    'comment 5': (4, 4),
    'comment 6': (5, 4),
    'toolbox 1': (7, 4),
    'toolbox 2': (7, 6),
    'toolbox 3': (8, 4),
    'toolbox 4': (8, 6),
    'toolbox 5': (9, 4),
    'toolbox 6': (9, 6),
    'toolbox 7': (10, 4),
    'toolbox 8': (10, 6),
    'weather condition': (13, 4),
    'rain': (13, 6),
    'temp max': (13, 7),
    'temp min': (13, 8),
    'qc': (30, 4),
    'data qc': (30, 5),
    'geometry qc': (30, 6),
    'data shipped': (30, 8),
    'hse stop cards': (33, 5),
    'hse lti': (34, 5),
    'hse fac': (35, 5),
    'hse mtc': (36, 5),
    'hse RWC': (37, 5),
    'hse incident or nm': (33, 8),
    'hse medevac': (34, 8),
    'hse drills': (35, 8),
    'hse audits': (36, 8),
    'hse lsr violation': (37, 8),
    'ops time': (46, 3),
    'day time': (47, 3),
}

source_prod_schema = [
    'sp_t1_flat', 'sp_t2_rough', 'sp_t3_facilities', 'sp_t4_dunes',
    'sp_t5_sabkha', 'skips',
]

receiver_prod_schema = [
    'layout', 'pickup', 'qc_field', 'qc_camp', 'upload',
]

time_breakdown_schema = [
    'rec_hours', 'rec_moveup', 'logistics', 'camp_move', 'wait_source', 'wait_layout',
    'wait_shift_change', 'company_suspension', 'company_tests', 'beyond_control',
    'line_fault', 'instrument_fault', 'vibrator_fault', 'incident', 'holiday',
    'recovering', 'other_downtime',
]

ops_time_keys = [
    'rec_hours', 'rec_moveup', 'logistics', 'wait_source', 'wait_layout',
    'wait_shift_change',
]

standby_keys = ['company_suspension', 'company_tests', 'beyond_control', 'camp_move']

downtime_keys = [
    'line_fault', 'instrument_fault', 'vibrator_fault', 'incident', 'holiday',
    'recovering', 'other_downtime',
]

hse_weather_schema = [
    'stop', 'lti', 'fac', 'mtc', 'rwc', 'incident_nm', 'medevac', 'drills', 'audits',
    'lsr_violations', 'ops_time', 'day_time', 'weather_condition', 'rain',
    'temp_min', 'temp_max',
]

WEEKDAYS = 7
WEEKS = 6
AVG_PERIOD = 14
STOP_TARGET = (9, 9)
PROD_TARGET = (0.9, 1)
REC_TARGET = (21, 22)
NO_DATE_STR = '-'
RIGHT_ARROW = '\u25B6'
LEFT_ARROW = '\u25C0'
SS_2 = '\u00B2'  # superscript 2 for like km2
NAME_LENGTH = 20
DESCR_LENGTH = 100
TYPE_LENGTH = 10
COMMENT_LENGTH = 5000
WIDGET_WIDTH_PROJECT_FIELDS = 'width:100px'
