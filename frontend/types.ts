// ============================================================
// TEST AI - SHARED FRONTEND TYPES
// ============================================================

export type TestStatus =
  | "PASS"
  | "HEALED"
  | "FAIL"
  | "SKIPPED";

// ============================================================
// LOCATOR
// ============================================================

export interface LocatorTarget {
  role?: string;
  name?: string;
  label?: string;
  css?: string;
  id?: string;
  nameAttr?: string;
  placeholder?: string;
  tag?: string;
  text?: string;
}

// ============================================================
// TEST STEPS
// ============================================================

export type StepAction =
  | "navigate"
  | "click"
  | "input"
  | "select"
  | "wait"
  | "verify_url"
  | "verify_text"
  | "verify_element";

export interface TestStep {
  action: StepAction | string;
  target?: LocatorTarget;
  value?: string;
  url?: string;
  ms?: number;
}

// ============================================================
// VERIFICATIONS
// ============================================================

export type VerificationType =
  | "url"
  | "text"
  | "page_title"
  | "element";

export interface VerificationStep {
  type: VerificationType;
  condition?: "contains" | "equals";
  value?: string;
  target?: LocatorTarget;
}

// ============================================================
// PROJECT
// ============================================================

export interface Project {
  id: string;
  name: string;
  target_url: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

// ============================================================
// TEST CASE
// ============================================================

export interface TestCase {
  id: string;
  project_id: string;
  name: string;
  target_url: string;
  steps: TestStep[];
  verifications: VerificationStep[];
  created_at?: string;
  updated_at?: string;
}

// ============================================================
// HEALING
// ============================================================

export interface HealingDetails {
  healed?: boolean;

  original_locator?:
    | string
    | LocatorTarget;

  replacement_locator?:
    | string
    | LocatorTarget;

  confidence?: number;
  reason?: string;
}

// ============================================================
// RUN STEP
// ============================================================

export interface RunStepResult {
  step?: number;
  action?: string;
  status?: TestStatus;
  message?: string;

  target?: LocatorTarget;

  value?: string;
  url?: string;

  screenshot?: string;
  screenshot_path?: string;

  started_at?: string;
  finished_at?: string;

  duration_ms?: number;

  healing?: HealingDetails;

  original_locator?:
    | string
    | LocatorTarget;

  replacement_locator?:
    | string
    | LocatorTarget;

  confidence?: number;
  reason?: string;

  error?: string;
}

// ============================================================
// VERIFICATION RESULT
// ============================================================

export interface VerificationResult {
  type?: string;
  status?: TestStatus;

  condition?: string;

  expected?: string;
  actual?: string;

  value?: string;

  message?: string;

  screenshot?: string;

  error?: string;
}

// ============================================================
// EVIDENCE
// ============================================================

export interface RunEvidence {
  type: string;
  url: string;
  name: string;

  step?: number;
  verification?: number;
}

// ============================================================
// TEST RUN
// ============================================================

export interface TestRun {
  id: string;
  test_run_id?: string;

  test_case_id: string;

  test_name?: string;
  target_url?: string;

  status: TestStatus;

  message?: string;

  started_at?: string;
  finished_at?: string;

  duration_ms?: number;

  steps: RunStepResult[];

  verifications?: VerificationResult[];

  evidence?: RunEvidence[];

  healed?: boolean;

  healing_count?: number;

  healing_details?: HealingDetails[];

  error?: string;

  created_at?: string;

  test?: {
    id: string;
    name: string;
    target_url: string;
  };
}

// ============================================================
// API RESPONSES
// ============================================================

export interface ProjectsResponse {
  projects: Project[];
}

export interface TestsResponse {
  tests: TestCase[];
  total?: number;
}

export interface TestResponse {
  message?: string;
  test: TestCase;
}

export interface RunsResponse {
  runs: TestRun[];
  total?: number;
}

export interface RunResponse {
  message?: string;
  run: TestRun;
}

// ============================================================
// AUTH
// ============================================================

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface SignupResponse {
  message: string;
  user: User;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============================================================
// DASHBOARD
// ============================================================

export interface DashboardStats {
  total_projects: number;
  total_tests: number;
  total_runs: number;
  passed_runs: number;
  healed_runs: number;
  failed_runs: number;
}

// ============================================================
// RECORDER
// ============================================================

export interface RecorderSession {
  session_id?: string;
  id?: string;

  project_id: string;
  target_url: string;

  name?: string;

  status?: string;

  events?: RecorderEvent[];

  started_at?: string;
  finished_at?: string;
}

export interface RecorderEvent {
  type?: string;
  action?: string;

  timestamp?: string;

  url?: string;
  value?: string;

  ms?: number;

  target?: LocatorTarget;
}