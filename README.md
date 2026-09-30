# Slot Machine Backend

A Python-based slot machine backend built with FastAPI.

The project started as a command-line slot machine and was later developed into a REST API with session management, balance handling, persistent database storage, game logic, input validation, concurrency handling, historical player data, admin statistics, and file exports.

The backend uses SQLite with SQLAlchemy to persist users, game sessions, bets, and deposits.

## Setup and Running

### 1. Clone the repository

```bash
git clone https://github.com/forrealayush/slotmachine.git
cd slotmachine
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the API

```bash
uvicorn api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 4. Open the API documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger UI can be used to interact with the API and test its endpoints.

## Features

* Create users and unique game sessions using UUIDs
* Persistent user and game data using SQLite
* SQLAlchemy ORM for database interaction
* Deposit funds into player accounts
* Place bets from ₹500 to ₹10,000 per payline
* Choose between 1 and 5 paylines
* Generate weighted slot symbols
* Five paylines using rows and diagonals
* Wild symbol support
* Jackpot multipliers for matching symbols
* Persistent bet and deposit history
* Player betting history and aggregate statistics
* Casino-wide admin statistics
* Per-player admin activity overview
* CSV player data export
* JSON player data export
* Per-session locking for concurrent balance updates
* Input validation with appropriate HTTP status codes
* Automated tests for validation and concurrent requests
* Interactive API documentation through Swagger UI

## Database

The project uses SQLite as its database and SQLAlchemy as the ORM.

The database contains persistent data for:

* Users
* Game sessions
* Bets
* Deposits

The database is created locally as `casino.db` and is excluded from Git using `.gitignore`.

The main relationships are:

```text
User
 ├── GameSession
 │    └── Bet
 └── Deposit
```

This allows historical game activity to be retrieved and aggregated rather than relying only on in-memory session data.

## Game Rules

* **A, B, C, D, W** are the available symbols.

* `W` is a wild symbol and can substitute for other symbols when checking a winning line.

* There are **5 paylines** available: 3 horizontal and 2 diagonal.

* Win multipliers:

  * `D` ×2
  * `C` ×3
  * `B` ×4
  * `A` ×5
  * `W` ×10

* A line containing `W-W-W` is classified as a **jackpot**.

* Winning lines with wild substitutions, such as `C-W-C`, are treated as regular wins.

## Project Structure

```text
slotmachine/

├── api.py
├── database.py
├── models.py
├── slotmachine2.py
├── requirements.txt
├── README.md
├── game/
│   ├── __init__.py
│   └── engine.py
└── tests/
    ├── test_concurrency.py
    └── test_validation.py
```

### Main files

* `api.py` contains the FastAPI application, API endpoints, database session handling, game sessions, deposits, player history, admin statistics, and data exports.
* `database.py` contains the SQLAlchemy database engine and database session configuration.
* `models.py` defines the SQLAlchemy database models and relationships.
* `game/engine.py` contains the slot machine logic, symbol generation, paylines, and winnings calculation.
* `slotmachine2.py` contains the original command-line version of the slot machine.
* `tests/` contains the automated API tests.
* `requirements.txt` contains the Python packages required to run the project.

## API Flow

A typical game flow works like this:

1. Register a user using `POST /register`.
2. Create a game session using `POST /session`.
3. Deposit funds using `POST /session/{session_id}/deposit`.
4. Play the game using `GET /game`.
5. The API generates the slot result and calculates winnings.
6. The user's balance is updated.
7. The bet is stored in the database for historical tracking.
8. Player and admin endpoints can later retrieve and aggregate the stored data.

Balance updates are protected by a lock for the active game session so that concurrent requests for the same session do not overwrite each other's changes.

## API Endpoints

### `GET /`

Returns a simple message confirming that the API is running.

### `POST /register`

Creates a new player.

The current implementation creates a player with the default `player` role.

### `POST /session`

Creates a new game session for an existing user.

Returns a unique session ID and the user's current balance.

### `POST /session/{session_id}/deposit`

Adds funds to the user's balance.

The minimum deposit amount is ₹500.

Deposits are stored in the database.

### `GET /game`

Plays the slot machine for a session.

Parameters:

* `session_id`: The ID of the game session
* `bet`: Amount bet per payline, from ₹500 to ₹10,000
* `lines`: Number of paylines to play, from 1 to 5

The endpoint returns the generated slot result, bet amount, number of paylines, winnings, winning lines, and updated balance.

### `GET /player/{username}/history`

Returns a player's historical betting activity and aggregate statistics.

The response includes:

* Total amount wagered
* Total winnings
* Net result
* Current balance
* Individual bet history

### `GET /player/{username}/deposits`

Returns the player's historical deposit records.

### `GET /admin/stats`

Returns aggregate casino statistics.

The endpoint provides:

* All-time statistics
* Today's statistics
* Statistics for a configurable number of previous days
* Number of players
* Number of spins
* Total amount wagered
* Total winnings
* Casino net result

Example:

```text
/admin/stats?days=30
```

### `GET /admin/players`

Returns an activity overview for every player.

The response includes:

* Username
* Number of spins
* Total amount wagered
* Total winnings
* Net result

### `GET /admin/players/export`

Generates a CSV file containing player activity data.

### `GET /admin/players/export/json`

Generates a JSON file containing player activity data.

## Concurrency Handling

The API can receive multiple requests for the same session at the same time.

Session balance updates are protected using a separate `Lock` for each session. This prevents two requests from reading and updating the same session balance simultaneously and potentially overwriting each other's changes.

Different sessions have separate locks, so a request for one session does not block another session.

The concurrency tests send multiple requests and verify that the resulting balances match the expected results.

## Testing

The project uses `pytest` for automated testing.

The tests cover:

* Valid game requests
* Invalid bet amounts
* Invalid numbers of paylines
* Invalid sessions
* Insufficient balance
* Deposits
* Invalid deposit amounts
* Invalid deposit sessions
* Unique session IDs
* Invalid balance requests
* Concurrent requests

Run the tests with:

```bash
pytest
```

## File Export

The backend can generate reports from the database.

Player activity can be exported as:

* CSV using `/admin/players/export`
* JSON using `/admin/players/export/json`

Generated export files are intentionally excluded from Git using `.gitignore`.

## Current Limitations

* Password handling is currently temporary and authentication has not yet been implemented.
* API endpoints are not yet protected by authentication or role-based authorization.
* Admin endpoints are currently accessible without admin authentication.
* Game session validity is partly maintained in server memory.
* Session locks are maintained in server memory.
* The API currently does not have a frontend.
* The API is currently intended to run locally.
