from celery import group
from logging import getLogger

from _plc_lines import celery_app as app
from devices.models import PLC


log = getLogger(__name__)


@app.task
def read_plc(plc_id: int):
    log.debug(f"{plc_id=}")
    plc = PLC.objects.get(id=plc_id)
    log.debug(f"{plc=}")
    value = plc.read()
    log.debug(f"{value=}")
    read_successful = value is not None and value == plc.expected_value
    log.info(f"{plc_id=}, {read_successful=}")
    plc.process_status(read_successful)


@app.task
def fanout_read_all_plcs():
    reading_group = group([
        read_plc.signature((plc_id,))
        for plc_id in PLC.objects.all().values_list('id', flat=True)
    ])
    reading_group.apply_async()
