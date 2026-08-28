import { useState } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Paper from "@mui/material/Paper";
import { useTheme } from "@mui/material/styles";
import { API } from "../../config/api.js";
import { apiFetch } from "../../services/api.js";
import { isAdmin as checkIsAdmin } from "../../services/auth.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAppData } from "../../context/AppDataContext.jsx";
import { useNotification } from "../../components/notificationController.tsx";
import ManageTechnologyDomains from "../../components/settings/ManageTechnologyDomains.jsx";
import AddFeedForm from "../../components/settings/AddFeedForm.jsx";
import FeedManager from "../../components/settings/FeedManager.jsx";
import SectionTitle from "../../components/settings/SectionTitle.jsx";
import SettingsDeleteButton from "../../components/settings/SettingsDeleteButton.jsx";
import SettingsAddButton from "../../components/settings/SettingsAddButton.jsx";
import ConfirmDeleteDialog from "../../components/settings/ConfirmDeleteDialog.jsx";
import CustomLoader from "../../components/CustomLoader.jsx";

export default function SettingsPage() {
  const theme = useTheme();
  const { showNotification } = useNotification();
  const { sessionEmployee } = useAuth();
  const {
    feeds,
    technologyDomains,
    recipients,
    recipientsLoading,
    feedsLoading,
    setRecipients,
    fetchFeeds,
    fetchTechnologyDomains,
  } = useAppData();

  const userIsAdmin = checkIsAdmin(sessionEmployee);
  const [settingsRefresh, setSettingsRefresh] = useState(0);
  const [domainsLoading, setDomainsLoading] = useState(true);
  const [domainsBusy, setDomainsBusy] = useState(false);
  const [feedsBusy, setFeedsBusy] = useState(false);
  const [feedFormBusy, setFeedFormBusy] = useState(false);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [validationError, setValidationError] = useState("");

  const recipientsBusy = adding || removing !== null;
  const settingsLoading =
    recipientsLoading
    || domainsLoading
    || feedsLoading
    || domainsBusy
    || feedsBusy
    || feedFormBusy
    || recipientsBusy;

  const validEmail = (e) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

  const handleFeedsChange = async () => {
    await fetchFeeds();
    setSettingsRefresh((token) => token + 1);
  };

  const handleAddRecipient = async () => {
    const email = input.trim().toLowerCase();
    if (!email) {
      setValidationError("Email is required");
      return;
    }
    if (!validEmail(email)) {
      setValidationError("Please enter a valid email address");
      return;
    }
    setValidationError("");
    setAdding(true);
    try {
      const created = await apiFetch(API.emails, {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setRecipients((prev) => [created, ...prev]);
      setInput("");
      showNotification({
        severity: "success",
        description: `Recipient "${email}" added`,
      });
    } catch (e) {
      const msg = String(e?.message || "");
      let description = `Unable to add recipient: ${msg}`;
      if (msg.includes("409")) description = "This email recipient already exists";
      else if (msg.includes("422")) description = "Please enter a valid email address";
      showNotification({ severity: "error", description });
    } finally {
      setAdding(false);
    }
  };

  const handleConfirmRemoveRecipient = async () => {
    if (!deleteTarget) return;
    const target = deleteTarget;
    setDeleteTarget(null);
    setRemoving(target.id);
    try {
      await apiFetch(`${API.emails}/${target.id}`, { method: "DELETE" });
      setRecipients((prev) => prev.filter((r) => r.id !== target.id));
      showNotification({
        severity: "success",
        description: `Recipient "${target.email}" removed`,
      });
    } catch (e) {
      const msg = String(e?.message || "");
      showNotification({
        severity: "error",
        description: msg.includes("404")
          ? "Recipient was already removed"
          : `Unable to remove recipient: ${msg}`,
      });
    } finally {
      setRemoving(null);
    }
  };

  return (
    <Paper elevation={0} className="settings-layout-panel">
      <Box
        className={`settings-layout-body settings-layout-body--relative${settingsLoading ? " settings-layout-body--blocked" : ""}`}
      >
        {settingsLoading && <CustomLoader />}
        <Box className="settings-card-grid">
          <Paper variant="outlined" className="settings-card">
            <ManageTechnologyDomains
              onTechnologyDomainsChange={fetchTechnologyDomains}
              onFeedsChange={handleFeedsChange}
              onLoadingChange={setDomainsLoading}
              onBusyChange={setDomainsBusy}
              isAdmin={userIsAdmin}
              refreshToken={settingsRefresh}
            />
          </Paper>

          <Paper variant="outlined" className="settings-card">
            <AddFeedForm
              technologyDomains={technologyDomains}
              onAdd={handleFeedsChange}
              onBusyChange={setFeedFormBusy}
              isAdmin={userIsAdmin}
              feeds={feeds}
            >
              <FeedManager
                feeds={feeds}
                technologyDomains={technologyDomains}
                onFeedsChange={handleFeedsChange}
                onBusyChange={setFeedsBusy}
                isAdmin={userIsAdmin}
              />
            </AddFeedForm>
          </Paper>

          {userIsAdmin && (
            <Paper variant="outlined" className="settings-card">
              <Box className="settings-card-inner">
                <SectionTitle>Email Recipients</SectionTitle>
                <Box className="settings-add-row">
                  <TextField
                    size="small"
                    fullWidth
                    value={input}
                    onChange={(e) => {
                      setInput(e.target.value);
                      setValidationError("");
                    }}
                    onKeyDown={(e) => e.key === "Enter" && handleAddRecipient()}
                    placeholder="Email address"
                    error={Boolean(validationError)}
                    helperText={validationError || " "}
                  />
                  <SettingsAddButton onClick={handleAddRecipient} disabled={adding}>
                    {adding ? "Adding…" : "Add Email"}
                  </SettingsAddButton>
                </Box>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                  {!recipientsLoading && recipients.length === 0 ? (
                    <Typography
                      variant="body2"
                      className="settings-muted-text"
                      textAlign="center"
                      py={1.5}
                    >
                      No recipients configured
                    </Typography>
                  ) : (
                    recipients.map((recipient) => (
                      <Paper
                        key={recipient.id}
                        variant="outlined"
                        className="settings-list-item"
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1.25,
                          px: 1.5,
                          py: 0.875,
                        }}
                      >
                        <Box
                          sx={{
                            width: 6,
                            height: 6,
                            borderRadius: "50%",
                            bgcolor: recipient.is_enabled
                              ? theme.palette.success.main
                              : theme.palette.text.secondary,
                            flexShrink: 0,
                          }}
                        />
                        <Typography variant="body2" className="settings-body-text" sx={{ flex: 1 }}>
                          {recipient.email}
                        </Typography>
                        <SettingsDeleteButton
                          onClick={() => setDeleteTarget(recipient)}
                          title="Remove recipient"
                        />
                      </Paper>
                    ))
                  )}
                </Box>
              </Box>
            </Paper>
          )}
        </Box>
        <ConfirmDeleteDialog
          open={Boolean(deleteTarget)}
          title="Remove recipient"
          message={
            deleteTarget
              ? `Are you sure you want to remove "${deleteTarget.email}"?`
              : ""
          }
          confirmLabel="Remove"
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleConfirmRemoveRecipient}
        />
      </Box>
    </Paper>
  );
}
