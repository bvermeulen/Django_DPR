# common variables for seismicreport

TCF_table = {
    'flat': 0.85,
    'rough': 0.50,
    'facilities': 0.55,
    'dunes': 0.60,
    'sabkha': 0.6,
}

BGP_DR_table = {
    'date': (0, 1),
    'seq_report': (1, 1),
    'crew': (2, 1),
    'project': (3, 1),
    'block': (3, 5),
    'sp_t1': (6, 3),
    'sp_t2': (7, 3),
    'sp_t3': (8, 3),
    'sp_t4': (9, 3),
    'sp_t5': (10, 3),
    'tcf': (12, 1),
    'skips': (13, 1),
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
    'line fault': (100, 1),    # not used
    'instrument fault': (38, 1),
    'vibrator fault': (39, 1),
    'incident': (40, 1),
    'holiday': (41, 1),
    'recovering': (42, 1),
    'other dt': (43, 1),
    'layout': (47, 11),
    'pickup': (48, 11),
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
    'hse stop cards': (33, 11),
    'hse lti': (34, 11),
    'hse fac': (35, 11),
    'hse mtc': (36, 11),
    'hse RWC': (37, 11),
    'hse incident or nm': (34, 14),
    'hse medevac': (35, 14),
    'hse drills': (36, 14),
    'hse audits': (37, 14),
    'hse lsr violation': (38, 14),
    'ops time': (47, 9),
    'day time': (48, 9),
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

CTM_METHOD = 'Legacy'
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
IMG_SIZE = (310, 248)
NAME_LENGTH = 20
DESCR_LENGTH = 100
TYPE_LENGTH = 10
COMMENT_LENGTH = 5000
WIDGET_WIDTH_PROJECT_FIELDS = 'width:100px'
