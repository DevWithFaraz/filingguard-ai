# FilingGuard AI - Microsoft Word Add-in

This directory contains the canonical Office Web Add-in integration surface for FilingGuard AI, conforming to Office.js and the Office 1.1 XML manifest schema.

## Features

- **Direct Authoring Review**: Scan open Word document paragraphs directly from the Word ribbon without leaving Microsoft Word.
- **Document Synchronization**: Clicking any finding in the taskpane automatically navigates to and highlights the corresponding paragraph or passage in the Word document.
- **TLS & Token Authorization**: Connects directly to the FilingGuard REST API using ephemeral bearer tokens or claimed reviewer accounts.
- **Multi-Platform Support**: Runs in Word for Windows, Word for Mac, and Word on the Web (Office Online).

## File Structure

- `manifest.xml`: Standardized Office 1.1 Add-in XML manifest registering the `FilingGuard Review` ribbon button.
- `taskpane.html`: Sandboxed taskpane HTML view with Content Security Policy protection.
- `taskpane.js`: Office.js integration script handling paragraph extraction, API submission, polling, and bidirectional selection.
- `taskpane.css`: Taskpane visual styling matching the FilingGuard brand and Apple/Office design guidelines.

## Sideloading Instructions

### Word on the Web (Office Online)
1. Open a document in Word on the Web.
2. Go to **Insert** > **Add-ins** > **Upload My Add-in**.
3. Browse and select `manifest.xml`.
4. Click the **FilingGuard** tab on the ribbon and click **Audit Filing**.

### Word for Windows (Desktop)
1. Share the `integrations/office-addin/` folder as a Windows network share or register it as a Trusted Add-in Catalog in Word Options (`File > Options > Trust Center > Trust Center Settings > Trusted Add-in Catalogs`).
2. Restart Word, navigate to **Insert > My Add-ins > Shared Folder**, and select **FilingGuard Pre-Filing Review**.

## Security Guidelines

- Never hardcode API tokens into `taskpane.html` or `taskpane.js`.
- All network communication must use HTTPS in production.
- Raw filing text is transmitted solely to the authenticated FilingGuard API instance and is governed by session retention policies.
