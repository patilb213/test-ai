# 🧪 Test AI
### AI-Assisted Smart Test Recording and Self-Healing Verification System

**Record. Automate. Verify. Heal.**

Test AI is a web-based testing platform that helps users record website actions, save automated test cases, verify expected results, and identify changes in website elements using AI-assisted self-healing.

The project combines browser automation, artificial intelligence, and a user-friendly dark-themed interface.

## 🌐 Project Links

| Resource | Link |
|---|---|
| Live Website | [Test AI](https://test-7msv6pn0z-acme-a982.vercel.app) |
| Backend API | [Render](https://test-ai-sxhg.onrender.com) |
| API Documentation | [Swagger UI](https://test-ai-sxhg.onrender.com/docs) |
| GitHub Repository | [Source Code](https://github.com/patilb213/test-ai) |

**Deployment status:** The frontend and backend have been deployed. Complete end-to-end functionality on the public deployment has not yet been verified.

---

## 📖 About the Project

Testing a website means checking whether its buttons, pages, and other features work correctly.

For example, when someone clicks a login button, the website should respond as expected.

Test AI makes this process easier by allowing users to record browser actions and save them as reusable test cases.

When a website changes, Test AI can also attempt to identify the correct element using alternative locators and AI-based semantic similarity.

## 🎯 Project Objective

To develop an AI-assisted web testing platform that reduces repetitive manual testing and helps automated tests handle certain website interface changes.

---

## ✨ Implemented Modules

### 1. User Authentication

- User signup and login APIs.
- Token-based authentication.
- Frontend login and signup pages.
- Successful local login and dashboard navigation.

### 2. Dashboard

- Dark-themed dashboard interface.
- Navigation to the application's testing modules.
- Access to projects, recording, tests, runs, reports, and healing pages.

### 3. Project Management

- Project creation through the backend API.
- Project listing in the frontend.
- Storage of project information in MongoDB Atlas.
- Successful local project creation and retrieval.

### 4. Test Recorder

- Browser action recording functionality.
- Collection of information about recorded elements.
- Saving recorded actions as test cases.
- Successful local test recording and saving.

### 5. Test Case Management

- Display of saved test cases.
- Storage of recorded test steps.
- Expected-result configuration.
- Individual test detail pages.

### 6. Expected Result Verification

Test AI supports configured checks such as:

- URL verification.
- Page text verification.
- Element existence verification.

These checks help determine whether a test produced the expected result.

### 7. Automated Test Runner

The backend uses Playwright to execute saved browser actions.

Implemented functionality includes:

- Navigating to target websites.
- Finding recorded page elements.
- Executing supported recorded actions.
- Processing execution outcomes.
- Recording step-level results.

### 8. AI-Assisted Self-Healing

The self-healing engine attempts to recover when an original recorded element cannot be located.

Implemented components include:

- Original locator resolution.
- Alternative locator generation.
- Candidate element evaluation.
- Semantic similarity scoring.
- Confidence-based recovery decisions.
- Automatic recovery for accepted candidates.
- Review-required outcomes for uncertain candidates.

The semantic matching implementation uses SentenceTransformers.

**Important:** Self-healing does not guarantee recovery from every website change.

### 9. Healing Approval System

- Backend healing approval logic.
- Four healing approval API endpoints.
- Dark-themed Healing Approval Dashboard.
- Review workflow for healing suggestions requiring approval.

### 10. Test Runs

- Test run listing page.
- Individual run detail page.
- Step execution results.
- Healing-related run information.
- Tracking of successful and failed execution steps.

### 11. Reports

- Dark-themed reports page.
- Test execution information.
- AI healing and review-event information.

### 12. Evidence Security Configuration

The backend includes the following configuration:

```env
ENABLE_PUBLIC_EVIDENCE=false
```

Public evidence access is configured to remain disabled. Production authorization and evidence access still require end-to-end verification.

---

## 🧠 How AI Self-Healing Works

Consider a website with a button named:

**Log in**

A test is recorded to click that button.

Later, the website changes the button name to:

**Sign in**

The recorded locator may no longer match the original button.

Test AI attempts to:

1. Locate the original element.
2. Search for alternative elements.
3. Evaluate possible matches.
4. Compare semantic similarity.
5. Automatically recover when the candidate satisfies the healing checks, or request review when uncertain.
6. Record the result in the test run.

### Verified Local Healing Scenario

| Detail | Result |
|---|---|
| Original button | Log in |
| Updated button | Sign in |
| Semantic similarity observed | Approximately 0.8589 |
| Healing engine | Executed |
| Review-required behavior | Observed |
| Successful healed run | Observed |

This demonstrates the AI-assisted recovery workflow on a locally tested website change.

---

## 🔬 Additional Test Scenario

A separate Northstar testing website was used to test changes in website elements.

| Version 1 | Version 2 |
|---|---|
| Explore products | View products |

The second version also introduced a change to the button's DOM structure.

The updated website was confirmed to display the new button. A successful healed result for this specific scenario has not yet been confirmed.

---

## 🏗️ System Architecture

```text
             USER
              |
              v
     Next.js Frontend
              |
              v
        FastAPI Backend
              |
       +------+------+
       |             |
       v             v
  MongoDB Atlas   Playwright
                     |
                     v
               Test Execution
                     |
                     v
              Healing Engine
                     |
                     v
               Run Results
```

### Simple Explanation

**Frontend:** The website users interact with.

**Backend:** Processes requests, runs tests, and performs healing operations.

**MongoDB Atlas:** Stores application data.

**Playwright:** Controls the browser to perform recorded actions.

**AI Healing Engine:** Evaluates possible replacement elements when a recorded locator fails.

---

## 🛠️ Technologies Used

| Technology | Usage |
|---|---|
| Next.js | Frontend application |
| React | Interactive interface |
| TypeScript | Frontend development |
| Tailwind CSS | Dark-themed styling |
| Python | Backend programming |
| FastAPI | Backend APIs |
| MongoDB Atlas | Database |
| Playwright | Browser automation |
| SentenceTransformers | Semantic similarity |
| JWT | Authentication |
| Git and GitHub | Version control |
| Vercel | Frontend hosting |
| Render | Backend hosting |

---

## 📁 Project Structure

```text
test-ai/
├── frontend/
│   └── app/
│       ├── login/
│       ├── signup/
│       ├── dashboard/
│       ├── projects/
│       ├── recorder/
│       ├── tests/
│       ├── runs/
│       ├── reports/
│       └── healing/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── projects.py
│   │   ├── tests.py
│   │   ├── runner.py
│   │   ├── healing.py
│   │   ├── healing_scoring.py
│   │   ├── healing_approvals.py
│   │   ├── healing_routes.py
│   │   └── runs.py
│   └── requirements.txt
│
├── automation/
├── docs/
├── tests/
└── README.md
```

This structure highlights the main modules.

---

## 💻 Running the Project Locally

### Backend

Open PowerShell:

```powershell
cd backend

python -m venv venv

.\venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

python -m playwright install chromium
```

Create `backend/.env` and configure:

```env
MONGO_URL=your_mongodb_connection_string
DATABASE_NAME=test_ai
JWT_SECRET_KEY=your_secure_secret
ENABLE_PUBLIC_EVIDENCE=false
```

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Backend:

`http://localhost:8000`

Swagger documentation:

`http://localhost:8000/docs`

### Frontend

Open another terminal:

```powershell
cd frontend

npm install

npm run dev
```

Frontend:

`http://localhost:3000`

Configure the frontend's API URL according to the environment variable used in its source code.

---

## ☁️ Deployment Status

| Component | Platform | Status |
|---|---|---|
| Frontend | Vercel | Deployed |
| Backend | Render | Deployed |
| Database | MongoDB Atlas | Connected during local development |
| Source code | GitHub | Published |
| Complete production workflow | Vercel + Render | Not yet fully verified |

The Render deployment successfully started FastAPI and returned an HTTP 200 response.

The Vercel frontend deployment also completed successfully.

Production testing of authentication, recording, execution, database connectivity, and AI healing remains necessary.

---

## 📊 Implementation Status

| Feature | Status |
|---|---|
| Signup and login | Implemented and locally tested |
| Dashboard | Implemented |
| Project creation | Implemented and locally tested |
| Test recording | Implemented and locally tested |
| Save test case | Implemented and locally tested |
| Expected-result verification | Implemented |
| Playwright test execution | Implemented and locally tested |
| Semantic healing | Implemented and locally tested |
| Healing approval APIs | Implemented |
| Healing approval dashboard | Implemented |
| Test runs | Implemented |
| Reports | Implemented |
| GitHub publication | Completed |
| Backend deployment | Completed |
| Frontend deployment | Completed |
| Production end-to-end verification | Pending |

---

## 🔐 Security Notes

- Backend secrets are configured through environment variables.
- Authentication uses JWT-based tokens.
- Public evidence access is configured as disabled.
- AI healing includes a review-required workflow for uncertain recoveries.
- Only websites owned by the user or explicitly authorized for testing should be automated.

The application has not yet completed a comprehensive production security audit.

---

## 🎓 What This Project Demonstrates

Test AI demonstrates the integration of:

- Full-stack web development.
- REST API development.
- Cloud database connectivity.
- Browser automation.
- Test case recording.
- Expected-result verification.
- AI-based semantic matching.
- Human-reviewed healing decisions.
- Cloud deployment.

The project brings these capabilities together into one testing platform.

---

## 🏁 Conclusion

Test AI is an AI-assisted web testing platform that combines browser action recording, automated test execution, expected-result verification, and intelligent element recovery.

The implemented system includes authentication, project management, test recording, test cases, Playwright execution, AI semantic healing, healing approvals, runs, reports, and deployed frontend and backend services.

A successful local AI-healing scenario has been observed, while complete production end-to-end verification remains pending.

**Test AI — Record. Automate. Verify. Heal.**

---

[Live Website](https://test-7msv6pn0z-acme-a982.vercel.app) | [GitHub Repository](https://github.com/patilb213/test-ai)