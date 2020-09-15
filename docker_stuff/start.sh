python3 docker_add_dbs.py
cp ./default-nginx-config /etc/nginx/sites-available/default
cd api_gui
supervisord
service nginx restart
chmod -R 755 /var/dbs/
tail -f /dep_search/dep_search/api_gui/log
