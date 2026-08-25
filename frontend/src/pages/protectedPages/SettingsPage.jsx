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

export default function SettingsPage() {
  const theme = useTheme();
  const { showNotification } = useNotification();
  const { sessionEmployee } = useAuth();
  const {
    feeds,
    technologyDomains,
    recipients,
    recipientsLoading,
    setRecipients,
    fetchFeeds,
    fetchTechnologyDomains,
  } = useAppData();

  const userIsAdmin = checkIsAdmin(sessionEmployee);
  const [settingsRefresh, setSettingsRefresh] = useState(0);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [recError, setRecError] = useState("");

  const validEmail = (e) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

  const handleFeedsChange = async () => {
    await fetchFeeds();
    setSettingsRefresh((token) => token + 1);
  };

  const handleAddRecipient = async () => {
    const email = input.trim().toLowerCase();
    if (!email) {
      setRecError("Email is required");
      return;
    }
    if (!validEmail(email)) {
      setRecError("Please enter a valid email address");
      return;
    }
    setRecError("");
    setAdding(true);
    try {
      const created = await apiFetch(API.emails, {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setRecipients((prev) => [created, ...prev]);
      setInput("");
    } catch (e) {
      const msg = String(e?.message || "");
      if (msg.includes("409"))
        setRecError("This email recipient already exists");
      else if (msg.includes("422"))
        setRecError("Please enter a valid email address");
      else setRecError(`Unable to add recipient: ${msg}`);
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveRecipient = async (recipient) => {
    if (!confirm(`Remove "${recipient.email}"?`)) return;
    setRecError("");
    setRemoving(recipient.id);
    try {
      await apiFetch(`${API.emails}/${recipient.id}`, { method: "DELETE" });
      setRecipients((prev) => prev.filter((r) => r.id !== recipient.id));
      showNotification({
        severity: "success",
        description: `Recipient "${recipient.email}" removed`,
      });
    } catch (e) {
      const msg = String(e?.message || "");
      if (msg.includes("404")) setRecError("Recipient was already removed");
      else setRecError(`Unable to remove recipient: ${msg}`);
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
      <Box className="settings-layout-body">
        <Box className="settings-card-grid">
          <Paper variant="outlined" className="settings-card">
            <ManageTechnologyDomains
              onTechnologyDomainsChange={fetchTechnologyDomains}
              onFeedsChange={handleFeedsChange}
              isAdmin={userIsAdmin}
              refreshToken={settingsRefresh}
            />
          </Paper>

          <Paper variant="outlined" className="settings-card">
            <AddFeedForm
              technologyDomains={technologyDomains}
              onAdd={handleFeedsChange}
              isAdmin={userIsAdmin}
              feeds={feeds}
            >
              <FeedManager
                feeds={feeds}
                technologyDomains={technologyDomains}
                onFeedsChange={handleFeedsChange}
                isAdmin={userIsAdmin}
              />
            </AddFeedForm>
          </Paper>

          <Paper variant="outlined" className="settings-card">
            <Box className="settings-card-inner">
              <SectionTitle>Email Recipients</SectionTitle>
              {userIsAdmin && (
                <Box className="settings-add-row">
                  <TextField
                    size="small"
                    fullWidth
                    value={input}
                    onChange={(e) => {
                      setInput(e.target.value);
                      setRecError("");
                    }}
                    onKeyDown={(e) => e.key === "Enter" && handleAddRecipient()}
                    placeholder="Email address"
                    error={Boolean(recError)}
                  />
                  <SettingsAddButton onClick={handleAddRecipient} disabled={adding}>
                    {adding ? "Adding…" : "Add Email"}
                  </SettingsAddButton>
                </Box>
              )}
              {recError && (
                <Typography
                  variant="caption"
                  color="error"
                  sx={{ mb: 1, display: "block", fontSize: 14 }}
                >
                  {recError}
                </Typography>
              )}
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
                      {userIsAdmin && (
                        <SettingsDeleteButton
                          onClick={() => handleRemoveRecipient(recipient)}
                          loading={removing === recipient.id}
                          title="Remove recipient"
                        />
                      )}
                    </Paper>
                  ))
                )}
              </Box>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Paper>
  );
}
