.notif-page {
  background: #fafafa;
  min-height: 100vh;
  padding: 32px 24px 48px;
  color: #111827;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.notif-shell {
  max-width: 1440px;
  margin: 0 auto;
}
.notif-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 24px;
}
.notif-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
}
.notif-title {
  margin: 10px 0 8px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #111827;
}
.notif-subtitle {
  margin: 0;
  max-width: 760px;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.7;
}
.notif-meta-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}
.notif-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 10px 14px;
  color: #4b5563;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.notif-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 12px 24px rgba(16,24,40,.06);
}
.notif-toolbar {
  position: sticky;
  top: 16px;
  z-index: 20;
  margin-bottom: 24px;
}
.notif-toolbar-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
}
.notif-toolbar-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.notif-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.notif-kpi {
  padding: 18px 18px 16px;
}
.notif-kpi-label {
  color: #6b7280;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.notif-kpi-value {
  margin: 12px 0 8px;
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #111827;
}
.notif-kpi-note {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}
.notif-kpi-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #111827;
  font-size: 11px;
  font-weight: 700;
}
.notif-list-shell {
  padding: 8px;
}
.notif-list {
  display: grid;
  gap: 10px;
}
.notif-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: #ffffff;
  transition: all .15s ease;
}
.notif-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(16,24,40,.05), 0 14px 24px rgba(16,24,40,.08);
}
.notif-row.is-read {
  opacity: .72;
  background: #fcfcfd;
}
.notif-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}
.notif-marker {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 7px;
  flex-shrink: 0;
}
.notif-copy {
  min-width: 0;
}
.notif-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.notif-item-title {
  color: #111827;
  font-size: 16px;
  line-height: 1.35;
  font-weight: 700;
}
.notif-item-id {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}
.notif-meta {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.6;
}
.notif-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.notif-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid transparent;
}
.notif-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
  min-width: 110px;
}
.notif-age {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.notif-age-value {
  color: #111827;
  font-size: 32px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
}
.notif-age-label {
  color: #6b7280;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.notif-snooze {
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all .15s ease;
}
.notif-snooze:hover {
  background: #f9fafb;
}
.notif-empty {
  text-align: center;
  padding: 72px 24px;
}
.notif-empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  margin: 0 auto 16px;
  display: grid;
  place-items: center;
  background: #f3f4f6;
  color: #16a34a;
  font-size: 26px;
}
.notif-empty-title {
  color: #111827;
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 8px;
}
.notif-empty-copy {
  color: #6b7280;
  font-size: 14px;
}
.notif-banner {
  margin-bottom: 20px;
  border-radius: 18px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 700;
}
.notif-search-input {
  width: 240px;
  min-width: 220px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  background: #ffffff;
  outline: none;
}
.notif-search-input:focus {
  border-color: #cbd5e1;
  box-shadow: 0 0 0 3px rgba(37,99,235,.08);
}
.notif-select .Select-control,
.notif-select .Select-menu-outer {
  border-radius: 14px !important;
  border-color: #e5e7eb !important;
  box-shadow: none !important;
}
.notif-select .Select-control {
  min-height: 42px;
}
.notif-select .Select-placeholder,
.notif-select .Select-value-label,
.notif-select .Select-input > input {
  color: #111827 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
}
@media (max-width: 980px) {
  .notif-hero {
    flex-direction: column;
  }
  .notif-meta-stack {
    justify-content: flex-start;
  }
  .notif-row {
    grid-template-columns: 1fr;
  }
  .notif-side {
    align-items: flex-start;
    min-width: 0;
  }
}
