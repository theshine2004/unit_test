## Unit Testing Report

## 1. Tools used
- PyTest
- Coverage.py (pytest-cov)
- unittest.mock (MagicMock)
- SQLite in-memory (for unit tests involving database operations) 

## 2. Scope of testing

### 2.1 In Scope
- Validate_register function:
- Check email format
- Check password length
- Check and return a hash when the data is valid.
- Function search_movies_with_pagination: 
- Search by keyword (case-insensitive)
- Correct pagination of the number and total number of pages.
- Handling invalid page_size exception
- The send_chat_message function:
- Validate chat content
- Save data to the database
- Generate real-time events via websocket client (mock) - Ensure data rollback after each test

### 2.2 Out Scope
- Testing the integration of the Gateway API and real services - Testing high-load performance
- Frontend UI/UX testing
- In-depth security testing (SQL Injection, XSS, CSRF) 

## 3. Test Case Table
| Test Case ID | Objective | Input | Expected Output | Notes | 
|---|---|---|---|---|
| TC_UT_Minh_001 | Validate registration | email=minh.qa@example.com, password=StrongPass123 | Returns is_valid=True and a 64-bit hash string | Includes validation of email, password, and hashing |
| TC_UT_Minh_002 | Reject email with incorrect format |
email=minh-at-example.com, password=StrongPass123 | Returns is_valid=False, message="Email not in the correct format" | Validate email input |
| TC_UT_Minh_003 | Reject password too short | email=minh.qa@example.com, password=1234567 | Return is_valid=False, message="Password must be between 8 and 64 characters" | Validate minimum password length |
| TC_UT_Minh_004 | Checking hash stability |
plain_password=SamePassword! | Two hashes of the same input produce the same output | Confirm deterministic encryption logic |
| TC_UT_Minh_005 | Search for movies with pagination | keyword=batman, page=1, page_size=1 | total_items=2, total_pages=2, items[0].title="The Batman" | Comprehensive search + pagination |
| TC_UT_Minh_006 | Search with non-existent keyword |
keyword=not-found-keyword, page=1, page_size=5 | total_items=0, items=[] | Enclose empty data branch |
| TC_UT_Minh_007 | Catch invalid page_size error | keyword=batman, page=1, page_size=0 | Raise ValueError("page_size must be greater than 0") | Cover pagination parameter validation |
| TC_UT_Minh_008 | Chat sent successfully: saved to DB + emit realtime | sender_id=user_001, room_id=room_support, content valid | There is a record in the DB and ws_client.emit was called with the correct parameters | Used MagicMock to check realtime |
| TC_UT_Minh_009 | Reject empty chat | content=" " | Raise ValueError("Chat content cannot be empty"), do not emit | Cover validate input chat |
| TC_UT_Minh_010 | Check DB rollback after test | Insert temporary data in transaction test | Data only exists in the current test, rollback after test | Fixture setup/teardown type transaction |

## 4. Script Unit Test
- Test file: test_auth_utilities.py 
- Framework: PyTest + unittest.mock 
- Fixture DB:
- db_conn: create SQLite in-memory + schema
- db_transaction: BEGIN before test and ROLLBACK after test 

## 5. Execution Summary

### 5.1 Status
- Total number of test cases defined: 10
- Actual result: PASS 10/10
- Running time: 0.34 seconds
- Actual coverage: 99%

### 5.2 Notes on Actual Results
- Result of the command execution:


```text
..........                                                               [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.11.9-final-0 _______________

Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
test_auth_utilities.py     112      1    99%   119
------------------------------------------------------
TOTAL                      112      1    99%
10 passed in 0.34s
```

## 6. How to run tests and measure coverage
Install the library:


```bash
pip install pytest pytest-cov
```

Run the test and coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

Here are some tips for running the correct target file:

```bash
pytest test_auth_utilities.py --cov=test_auth_utilities --cov-report=term-missing
```

## 7. Conclusion

The current unit test suite covers the essential focus areas of the module:

- Validate email/password input data
- Password encryption logic
- Search for movies with pagination and error checking input.
- Real-time chat stream mockup
- CheckDB + Rollback model via fixture to ensure independent testing.
