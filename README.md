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

### 3. Set the secret key

Login tokens are signed with a secret key that is read from the `SLOT_SECRET_KEY` environment variable. The application will not start without it, and the key must never be committed to Git.

Generate a random key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then store it as an environment variable.

Windows (PowerShell), then open a new terminal:

```powershell
setx SLOT_SECRET_KEY "your-generated-key"
```

macOS / Linux:

```bash
export SLOT_SECRET_KEY="your-generated-key"
```

### 4. Create the database

The database schema is managed with Alembic migrations:

```bash
alembic upgrade head
```

This creates `casino.db` locally.

### 5. Start the API

```bash
uvicorn api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 6. Open the API documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger UI can be used to interact with the API. Use the **Authorize** button to log in and send your access token with requests.

### 7. Create the first admin

New users are always registered with the `player` role, and there is intentionally no API endpoint for becoming an admin. Register a user with `POST /register`, then promote it directly in the database:

```bash
python -c "import sqlite3; c=sqlite3.connect('casino.db'); c.execute('update users set role=? where username=?',('admin','your-username')); c.commit()"
```

The change takes effect immediately, because the role is read from the database on every request.

## Features

* Create users and unique game sessions using UUIDs
* Password hashing with Argon2
* Login with JWT access tokens
* Role-based authorization (`player` and `admin`)
* Players can only use their own sessions and view their own data
* Persistent user and game data using SQLite
* SQLAlchemy ORM for database interaction
* Database schema migrations using Alembic
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
* Per-user locking for concurrent balance updates
* Input validation with appropriate HTTP status codes
* Automated tests for validation, authentication, access control and concurrent requests
* Interactive API documentation through Swagger UI

## Database

The project uses SQLite as its database and SQLAlchemy as the ORM.

The database contains persistent data for:

* Users, including their password hash, role and balance
* Game sessions
* Bets
* Deposits

The schema is managed with Alembic. Running `alembic upgrade head` creates `casino.db` locally and applies any later schema changes without losing existing data. The database file is excluded from Git using `.gitignore`.

The balance belongs to the user, not to an individual game session.

The main relationships are:

```text
User
 ├── GameSession
 │    └── Bet
 └── Deposit
```

This allows historical game activity to be retrieved and aggregated rather than relying on in-memory data. Whether a game session is valid is decided by the database.

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
├── alembic.ini
├── README.md
├── alembic/
│   ├── env.py
│   └── versions/
├── game/
│   ├── __init__.py
│   └── engine.py
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_concurrency.py
    └── test_validation.py
```

### Main files

* `api.py` contains the FastAPI application, authentication and authorization, API endpoints, database session handling, game sessions, deposits, player history, admin statistics, and data exports.
* `database.py` contains the SQLAlchemy database engine and database session configuration.
* `models.py` defines the SQLAlchemy database models and relationships.
* `game/engine.py` contains the slot machine logic, symbol generation, paylines, and winnings calculation.
* `slotmachine2.py` is the original command-line version of the game.
* `alembic/` and `alembic.ini` contain the database migration setup and migration history.
* `tests/` contains the automated tests. `conftest.py` provides a test client and a temporary database for each test, so the tests do not need a running server and never touch `casino.db`.
* `requirements.txt` contains the Python packages required to run the project.

## API Flow

A typical game flow works like this:

1. Register a user using `POST /register` with a username and password. The password is stored only as an Argon2 hash.
2. Log in using `POST /login`. A successful login returns a JWT access token that expires after 30 minutes.
3. Send the token with every later request in the header `Authorization: Bearer <token>`. In Swagger UI, use the **Authorize** button.
4. Create a game session using `POST /session`. The session is created for the logged-in user.
5. Deposit funds using `POST /session/{session_id}/deposit`.
6. Play the game using `POST /game`.
7. The API generates the slot result and calculates winnings.
8. The user's balance is updated.
9. The bet is stored in the database for historical tracking.
10. Player and admin endpoints can later retrieve and aggregate the stored data.

The token contains only the username and an expiry time. On every request the server loads the user from the database, so the user's current role is always used.

Balance updates are protected by a lock for the user whose balance is being changed, so concurrent requests, including requests from different sessions of the same user, do not overwrite each other's changes.

## API Endpoints

| Endpoint | Access |
|---|---|
| `GET /` | Public |
| `POST /register` | Public |
| `POST /login` | Public |
| `GET /me` | Logged-in user |
| `POST /session` | Logged-in user |
| `POST /session/{session_id}/deposit` | Owner of the session |
| `POST /game` | Owner of the session |
| `GET /player/{username}/history` | That player, or an admin |
| `GET /player/{username}/deposits` | That player, or an admin |
| `GET /admin/stats` | Admin only |
| `GET /admin/players` | Admin only |
| `GET /admin/players/export` | Admin only |
| `GET /admin/players/export/json` | Admin only |

Requests without a valid token receive `401 Unauthorized`. A logged-in user who is not allowed to access an endpoint receives `403 Forbidden`. Using another user's session returns `404 Invalid session`, so the API does not reveal whether that session exists.

### `GET /`

Returns a simple message confirming that the API is running.

### `POST /register`

Creates a new player.

Request body (JSON):

```json
{"username": "alice", "password": "a-strong-password"}
```

The password is hashed with Argon2 before it is stored. New users always receive the `player` role. Returns `409` if the username is already taken.

### `POST /login`

Authenticates a user and returns an access token.

Send the `username` and `password` as form fields. The response contains an `access_token` and the `token_type` (`bearer`). Returns `401` for an incorrect username or password; the same message is used for both so the API does not reveal which usernames exist.

### `GET /me`

Returns the username and role of the logged-in user.

### `POST /session`

Creates a new game session for the logged-in user.

Returns a unique session ID, the username, and the user's current balance.

### `POST /session/{session_id}/deposit`

Adds funds to the user's balance.

The minimum deposit amount is ₹500. The session must belong to the logged-in user.

Deposits are stored in the database.

### `POST /game`

Plays the slot machine for a session that belongs to the logged-in user.

Parameters:

* `session_id`: The ID of the game session
* `bet`: Amount bet per payline, from ₹500 to ₹10,000
* `lines`: Number of paylines to play, from 1 to 5

The endpoint returns the generated slot result, bet amount, number of paylines, winnings, winning lines, and updated balance.

### `GET /player/{username}/history`

Returns a player's historical betting activity and aggregate statistics. Players can only view their own history; admins can view anyone's.

The response includes:

* Total amount wagered
* Total winnings
* Net result
* Current balance
* Individual bet history

### `GET /player/{username}/deposits`

Returns the player's historical deposit records. The same access rule as the betting history applies.

### `GET /admin/stats`

Returns aggregate casino statistics. Admin only.

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

Returns an activity overview for every player. Admin only.

The response includes:

* Username
* Number of spins
* Total amount wagered
* Total winnings
* Net result

### `GET /admin/players/export`

Generates a CSV file containing player activity data. Admin only.

### `GET /admin/players/export/json`

Generates a JSON file containing player activity data. Admin only.

## Concurrency Handling

The API can receive multiple requests at the same time, including several requests that change the same user's balance.

A user's balance belongs to the user, not to a game session. Balance updates are therefore protected by a `Lock` for each user. Inside the lock, the user is reloaded from the database so every update starts from the latest committed balance. This prevents two requests, even from two different sessions of the same user, from reading the same balance and overwriting each other's changes.

Different users have separate locks, so one user's request does not block another's.

The concurrency tests send simultaneous requests and verify that the final balances match the expected results, both for different users and for two sessions of the same user. These tests check correctness under concurrent requests. They do not measure performance.

## Testing

The project uses `pytest` for automated testing. The tests run against the application directly with a temporary database, so no server needs to be running and `casino.db` is never touched.

The tests cover:

* Registration, login and the `/me` endpoint
* Valid game requests
* Invalid bet amounts
* Invalid numbers of paylines
* Invalid sessions
* Insufficient balance
* Deposits
* Invalid deposit amounts
* Invalid deposit sessions
* Unique session IDs
* Requests without a token being rejected
* Users being unable to use another user's session
* Sessions remaining valid after the in-memory locks are reset
* Concurrent requests from different users
* Concurrent requests from different sessions of the same user

Run the tests from the project folder with:

```bash
python -m pytest
```

The admin endpoints, the player history access rules and the file exports have been tested manually through Swagger UI but do not yet have automated tests.

## File Export

The backend can generate reports from the database. Both exports are admin only.

Player activity can be exported as:

* CSV using `/admin/players/export`
* JSON using `/admin/players/export/json`

Each export is written to a uniquely named temporary file, sent to the client, and then deleted, so simultaneous exports cannot overwrite each other and no report files are left behind.

## Current Limitations

* Locks are kept in the memory of a single server process. If the API were run with several worker processes or servers, they would not share locks. A production version should make the database perform the balance update atomically.
* There is no logout, token refresh or token revocation. An access token stays valid until it expires after 30 minutes.
* There is no rate limiting on login attempts, and passwords are not checked for strength.
* The first admin has to be created by editing the database directly.
* Admin statistics and player reports are calculated with Python loops, and the aggregation logic is repeated across several endpoints. SQL aggregate queries and shared helper functions would be more efficient.
* The admin endpoints, history access rules and exports do not yet have automated tests.
* The project uses SQLite and is intended to run locally.
* The API does not have a frontend.