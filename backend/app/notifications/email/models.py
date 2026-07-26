from pydantic import BaseModel, ConfigDict, Field


class EmailRecipient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)

    def to_graph_payload(self) -> dict[str, dict[str, str]]:
        return {"emailAddress": {"address": self.email}}


class EmailAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    content_bytes_base64: str = Field(min_length=1)
    content_id: str | None = None
    is_inline: bool = False

    def to_graph_payload(self) -> dict[str, str | bool]:
        payload: dict[str, str | bool] = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": self.filename,
            "contentType": self.content_type,
            "contentBytes": self.content_bytes_base64,
            "isInline": self.is_inline,
        }
        if self.content_id:
            payload["contentId"] = self.content_id
        return payload


class EmailMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    html_body: str
    to_recipients: list[EmailRecipient] = Field(min_length=1)
    cc_recipients: list[EmailRecipient] = Field(default_factory=list)
    bcc_recipients: list[EmailRecipient] = Field(default_factory=list)
    attachments: list[EmailAttachment] = Field(default_factory=list)

    def to_graph_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "subject": self.subject,
            "body": {
                "contentType": "HTML",
                "content": self.html_body,
            },
            "toRecipients": [
                recipient.to_graph_payload() for recipient in self.to_recipients
            ],
        }
        if self.cc_recipients:
            payload["ccRecipients"] = [
                recipient.to_graph_payload() for recipient in self.cc_recipients
            ]
        if self.bcc_recipients:
            payload["bccRecipients"] = [
                recipient.to_graph_payload() for recipient in self.bcc_recipients
            ]
        if self.attachments:
            payload["attachments"] = [
                attachment.to_graph_payload() for attachment in self.attachments
            ]
        return payload
