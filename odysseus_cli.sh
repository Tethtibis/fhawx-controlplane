#!/usr/bin/env bash
# Odysseus CLI Dispatcher
case "${1:-status}" in
    start|on|up)
        /home/tethtibis/odysseus_ajax/start_service.sh
        ;;
    stop|off|down)
        /home/tethtibis/odysseus_ajax/stop_service.sh
        ;;
    status)
        /home/tethtibis/odysseus_ajax/status_service.sh
        ;;
    *)
        echo "Usage: odysseus {start|stop|status}"
        exit 1
        ;;
esac
