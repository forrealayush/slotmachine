# Slot Machine Backend

A Python based slot machine backend built with FastAPI.

The project started as a command line slot machine and was later developed into a REST API with session management, balance handling, game logic, input validation, and concurrent request handling.

The backend provides endpoints for creating game sessions, depositing funds, playing the slot machine, and checking the current session balance.

The project also includes automated tests for API validation, session behavior, and concurrent requests.

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

Open the following URL in a browser:

```text
http://127.0.0.1:8000/docs
```

Swagger UI can be used to create sessions, make deposits, play the game, and check balances.

## Features

* Create unique game sessions using UUIDs
* Deposit funds into a session with a minimum deposit of ₹500
* Place bets from ₹500 to ₹10,000 per payline
* Choose between 1 and 5 paylines
* Generate weighted slot symbols
* Five paylines using rows and diagonals
* Wild symbol support
* Jackpot multipliers for matching symbols
* Session specific balance management
* Per session locking for concurrent balance updates
* Input validation with appropriate HTTP status codes
* Automated tests for validation and concurrent requests
* Interactive API documentation through Swagger UI

## Project Structure

```text
slotmachine/
├── api.py
├── slotmachine2.py
├── requirements.txt
├── game/
│   ├── __init__.py
│   └── engine.py
└── tests/
    ├── test_concurrency.py
    └── test_validation.py
```

### Main files

* `api.py` contains the FastAPI application, session management, deposits, game endpoint, and balance handling.
* `game/engine.py` contains the slot machine logic, symbol generation, paylines, and winnings calculation.
* `slotmachine2.py` contains the original command line version of the slot machine.
* `tests/` contains the automated tests for the API.
* `requirements.txt` contains the Python packages required to run the project.

## API Flow

A typical game session works like this:

1. Create a session using `POST /session`.
2. Deposit funds using `POST /session/{session_id}/deposit`.
3. Play the game using `GET /game` with a session ID, bet amount, and number of paylines.
4. The API generates the slot result and calculates any winnings.
5. The session balance is updated.
6. Check the current balance using `GET /session/{session_id}`.

Each session has its own balance. Balance updates are protected by a lock for that specific session so that concurrent requests for the same session do not overwrite each other's changes.

## API Endpoints

### `GET /`

Returns a simple message to confirm that the API is running.

### `POST /session`

Creates a new game session and returns a unique session ID with an initial balance of ₹0.

### `POST /session/{session_id}/deposit`

Adds funds to an existing session.

The minimum deposit amount is ₹500.

### `GET /session/{session_id}`

Returns the current balance and session ID.

### `GET /game`

Plays the slot machine for a session.

Parameters:

* `session_id`: The ID of the game session
* `bet`: Amount bet per payline, from ₹500 to ₹10,000
* `lines`: Number of paylines to play, from 1 to 5

The endpoint returns the generated slot result, bet amount, number of paylines, winnings, winning lines, and updated balance.

Interactive API documentation is available through Swagger UI at `/docs` when the server is running locally.

## Concurrency Handling

The API can receive multiple requests for the same session at the same time.

Session balance updates are protected using a separate `Lock` for each session. This prevents two requests from reading and updating the same balance at the same time and potentially overwriting each other's changes.

Different sessions have separate locks, so a request for one session does not block balance updates for another session.

The concurrency test sends multiple requests across two sessions and checks that the final balances match the expected results.

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
* Concurrent requests across multiple sessions

Run the tests with:

```bash
pytest
```

The current test suite contains 11 tests.

## Current Limitations

* Session data is stored in server memory, so sessions are lost when the server restarts.
* The project currently does not use a database for persistent storage.
* The API currently does not have a frontend.
* The API is currently intended to run locally.
