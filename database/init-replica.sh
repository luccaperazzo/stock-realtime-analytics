#!/bin/bash
# Script para inicializar MongoDB Replica Set

echo "Esperando que MongoDB esté listo..."
sleep 10

echo "Inicializando Replica Set..."
mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "localhost:27017" }
  ]
})
'

echo "Replica Set inicializado correctamente"
