# Trip Calculator API

API principal do Trip Calculator, um MVP acadêmico para planejamento e estimativa de custos de viagens rodoviárias.

## Objetivo

Receber origem, destino, data, consumo do veículo, preço do combustível e pedágios; consultar distância e duração da rota; calcular combustível, custo de combustível e custo total; consultar o clima do destino; e salvar planejamentos em SQLite.

A API é a autoridade sobre validações e cálculos. O frontend não acessa provedores externos nem calcula os valores definitivos.

## Tecnologias e arquitetura

- Python 3.11 e Flask 3.
- Flask-SQLAlchemy com SQLite.
- Requests para integrações REST.
- Flask-CORS para comunicação com o frontend.
- Flask-OpenAPI3 para documentação interativa em `/openapi`.
- Docker.

Componentes: frontend web em HTML, CSS e JavaScript puro -> esta API REST/JSON -> serviços externos de rota/clima. O banco SQLite é uma camada de persistência interna, não um serviço separado.

## Estrutura

```text
trip-calculator-api/
├── app.py
├── database/database.py
├── models/trip.py
├── routes/trip_routes.py
├── services/calculation_service.py
├── services/route_service.py
├── services/weather_service.py
├── utils/validators.py
└── Dockerfile
```

## Instalação local

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

A API inicia em `http://localhost:5000`. A documentação interativa Swagger fica em `http://localhost:5000/openapi/` e a especificação OpenAPI em `http://localhost:5000/openapi/openapi.json`. A página inicial fica em `/` e o health check em `/health`.

## Variáveis de ambiente

- `DATABASE_URL`: padrão `sqlite:///trip_calculator.db`; no Docker usa `sqlite:////data/trip_calculator.db`.
- `CORS_ORIGINS`: origens separadas por vírgula.
- `EXTERNAL_API_TIMEOUT`: timeout em segundos.
- `EXTERNAL_API_USER_AGENT`: identificação enviada ao Nominatim.
- `GEOCODER_URL`, `ROUTER_URL` e `WEATHER_URL`: permitem trocar os provedores sem alterar as rotas públicas.

Nenhuma API key é necessária no MVP. Os limites e políticas dos serviços públicos devem ser respeitados, especialmente o User-Agent e o uso não abusivo do Nominatim.

## Docker

Execute os comandos a partir da raiz do projeto `trip-calculator-basic`. O volume preserva o banco SQLite entre reinicializações:

```bash
docker build -t trip-calculator-basic-api ./api
docker volume create trip-calculator-data
docker run -d --name trip-calculator-basic-api -p 5000:5000 -e CORS_ORIGINS=http://localhost:8080 -v trip-calculator-data:/data trip-calculator-basic-api

docker build -t trip-calculator-basic-front ./front
docker run -d --name trip-calculator-basic-front -p 8080:80 trip-calculator-basic-front
```

- Frontend: `http://localhost:8080`
- API: `http://localhost:5000`
- Swagger/OpenAPI: `http://localhost:5000/openapi/`
- Especificação OpenAPI JSON: `http://localhost:5000/openapi/openapi.json`
- Health check: `http://localhost:5000/health`
- SQLite: volume Docker `trip-calculator-data`, montado em `/data`.

## APIs externas

- **Nominatim / OpenStreetMap**: geocodificação textual de origem, destino e destino do clima. Serviço público, sem chave no MVP; consulte a política de uso do Nominatim.
- **OSRM**: rota de carro, distância em metros e duração em segundos. Serviço público baseado em dados OpenStreetMap.
- **Open-Meteo**: previsão diária por coordenadas, código meteorológico e temperatura máxima. Serviço público, sem chave para este uso; consulte os termos e atribuição do provedor.

As chamadas ficam encapsuladas em `route_service.py` e `weather_service.py`, com timeout e normalização interna. O frontend nunca chama os endpoints externos.

## Endpoints da API principal

### `GET /api/trips`

Lista planejamentos. Aceita `origin`, `destination` e `sort=total_cost|date`.

```json
{"data": [], "total": 0}
```

### `GET /api/trips/{id}`

Retorna uma viagem ou `404` com `{"error":"Trip not found"}`.

### `POST /api/trips`

Cria e persiste uma viagem. Exemplo:

```json
{"origin":"São Paulo, SP","destination":"Rio de Janeiro, RJ","travel_date":"2026-09-20","fuel_consumption":12.0,"fuel_price":6.2,"tolls":85.0}
```

Retorna `201` com `{"message":"Trip created successfully","trip":{...}}`.

### `POST /api/trips/calculate`

Usa o mesmo request, mas retorna somente a estimativa e não cria registro no banco.

### `PUT /api/trips/{id}`

Atualiza origem, destino, data, consumo, preço e pedágios. Os custos são recalculados pela API.

```json
{"fuel_consumption":11.5,"fuel_price":6.5,"tolls":90.0}
```

### `DELETE /api/trips/{id}`

Exclui a viagem e retorna `204 No Content`.

## Regras de negócio

```text
fuel_needed = round(distance_km / fuel_consumption, 2)
fuel_cost = round(fuel_needed * fuel_price, 2)
total_cost = round(fuel_cost + tolls, 2)
```

`origin`, `destination` e `travel_date` são obrigatórios. A data usa `YYYY-MM-DD`; consumo e preço devem ser maiores que zero; pedágios devem ser maiores ou iguais a zero. Falhas de validação retornam `400`. Se o clima estiver indisponível, a viagem continua válida e `weather`/`temperature` ficam nulos.


## Licença

Este projeto acadêmico não redistribui dados dos provedores. Consulte as licenças e políticas atuais do OpenStreetMap/Nominatim, OSRM e Open-Meteo antes de publicar ou operar em escala.
