python3 fill_dbs.py /data
/usr/bin/supervisord
/usr/sbin/nginx -g "daemon off;"
#
nginx -s reload
tail -f start.sh
