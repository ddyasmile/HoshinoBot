docker run  \
    --name nginx-static \
    -p 8070:8070 \
    -v /root/HoshinoBot/nginx:/etc/nginx/conf.d \
    -v /root/HoshinoBot/res:/home/static/res \
    -v /root/HoshinoBot/nginx/log:/var/log/nginx \
    -d nginx