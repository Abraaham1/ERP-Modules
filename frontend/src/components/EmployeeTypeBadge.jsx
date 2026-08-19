const LABELS = {
  swe: "Software Engineer",
  ml_engineer: "ML Engineer",
  devops_engineer: "DevOps Engineer",
  sqa: "SQA",
  db_analyst: "DB Analyst",
  backend_dev: "Backend Developer",
  frontend_dev: "Frontend Developer",
  cto: "CTO",
  cpdo: "CPDO",
};

export function employeeTypeLabel(type) {
  return LABELS[type] || type;
}

export default function EmployeeTypeBadge({ type }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-brand-50 text-brand-700 border border-brand-100">
      {employeeTypeLabel(type)}
    </span>
  );
}
