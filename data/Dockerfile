FROM mongo

COPY restaurant.json /restaurant.json

#ADD start.sh /start.sh
#RUN chmod +x /start.sh

CMD mongoimport -u root -p example --db prueba --collection restaurant --type json --file /restaurant.json
