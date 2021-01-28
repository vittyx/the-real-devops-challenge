#!/bin/bash
mongoimport -u root -p example --authenticationDatabase admin --db prueba --collection restaurant --file restaurant.json
