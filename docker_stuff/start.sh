/usr/bin/supervisord
/usr/sbin/nginx -g "daemon off;"
#
python3 fill_dbs.py /data
nginx -s reload
tail -f start.sh
