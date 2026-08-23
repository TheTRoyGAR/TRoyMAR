-- TRoyMAR (TRoy Maritime Agency) — D1 Database Schema

CREATE TABLE IF NOT EXISTS departments (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  agent_count INTEGER DEFAULT 5,
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  department TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  goal TEXT,
  status TEXT DEFAULT 'active',
  tasks_completed INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  department TEXT NOT NULL,
  agent TEXT,
  task TEXT NOT NULL,
  input TEXT,
  output TEXT,
  status TEXT DEFAULT 'queued',
  created_at TEXT,
  completed_at TEXT
);

-- Seed departments
INSERT OR IGNORE INTO departments (id, name, description, agent_count) VALUES
  ('orchestrator', 'Management', 'CEO Assistant — DELEGATE, REVIEW, FINAL_QA', 1),
  ('marketing', 'Marketing', 'Port intelligence, capability content, reputation — 5 agents', 5),
  ('sales', 'Sales', 'Agency appointments and brokerage — 5 agents', 5),
  ('finance', 'Finance', 'Disbursement accounts and billing — 5 agents', 5),
  ('shipping', 'Shipping & Ship Agency Operations', 'Port calls, husbandry, cargo & logistics — 6 agents', 6);

-- Seed agents
INSERT OR IGNORE INTO agents (id, department, name, role) VALUES
  ('mkt-1', 'marketing', 'marketing_head', 'Head of the AI Marketing Department'),
  ('mkt-2', 'marketing', 'port_intel_analyst', 'Port Intelligence Analyst'),
  ('mkt-3', 'marketing', 'content_creator', 'Content Creator'),
  ('mkt-4', 'marketing', 'industry_relations_manager', 'Industry Relations Manager'),
  ('mkt-5', 'marketing', 'reputation_analytics_reporter', 'Reputation & Analytics Reporter'),
  ('sales-1', 'sales', 'sales_head', 'Head of the AI Sales Department'),
  ('sales-2', 'sales', 'port_call_opportunity_finder', 'Port Call Opportunity Finder'),
  ('sales-3', 'sales', 'opportunity_qualifier', 'Opportunity Qualifier'),
  ('sales-4', 'sales', 'proposal_quote_writer', 'Proposal & Quote Writer'),
  ('sales-5', 'sales', 'appointment_closer', 'Appointment Closer'),
  ('fin-1', 'finance', 'finance_head', 'Head of the AI Finance Department'),
  ('fin-2', 'finance', 'disbursement_account_clerk', 'Disbursement Account Clerk'),
  ('fin-3', 'finance', 'budget_planner', 'Budget Planner'),
  ('fin-4', 'finance', 'invoice_manager', 'Invoice Manager'),
  ('fin-5', 'finance', 'cost_optimizer', 'Cost Optimizer'),
  ('ship-1', 'shipping', 'shipping_head', 'Head of Shipping & Ship Agency Operations'),
  ('ship-2', 'shipping', 'logistics_coordinator', 'Port Call Logistics Coordinator'),
  ('ship-3', 'shipping', 'customs_compliance_specialist', 'Customs & Compliance Specialist'),
  ('ship-4', 'shipping', 'husbandry_specialist', 'Vessel Husbandry Specialist'),
  ('ship-5', 'shipping', 'cargo_logistics_manager', 'Cargo & Logistics Manager'),
  ('ship-6', 'shipping', 'systems_integrator', 'Systems Integrator');
