import json
import io
from typing import Dict, Any

class ExportService:
    @staticmethod
    def to_markdown(meeting_dict: Dict[str, Any]) -> str:
        title = meeting_dict.get("title", "Meeting Summary")
        created_at = meeting_dict.get("created_at", "")
        exec_summary = meeting_dict.get("executive_summary", "No summary available.")
        decisions = meeting_dict.get("key_decisions", [])
        discussion_points = meeting_dict.get("discussion_points", [])
        action_items = meeting_dict.get("action_items", [])
        tags = meeting_dict.get("tags", [])
        sentiment = meeting_dict.get("sentiment", "Neutral")
        transcript = meeting_dict.get("transcript", "")

        md = []
        md.append(f"# {title}\n")
        md.append(f"**Date**: {created_at} | **Tone/Sentiment**: {sentiment}")
        if tags:
            md.append(f"**Tags**: {', '.join(f'`{t}`' for t in tags)}")
        md.append("\n---\n")

        md.append("## Executive Summary\n")
        md.append(f"{exec_summary}\n")

        if decisions:
            md.append("## Key Decisions Made\n")
            for d in decisions:
                md.append(f"- {d}")
            md.append("")

        if discussion_points:
            md.append("## Discussion Points & Topics\n")
            for p in discussion_points:
                md.append(f"- {p}")
            md.append("")

        if action_items:
            md.append("## Action Items & Next Steps\n")
            md.append("| Status | Task | Assignee | Priority | Due Date |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for item in action_items:
                status_icon = "x" if item.get("status") == "completed" else " "
                task = item.get("task", "")
                assignee = item.get("assignee", "Unassigned")
                priority = item.get("priority", "Medium")
                due = item.get("due_date", "TBD")
                md.append(f"| [{status_icon}] | {task} | {assignee} | {priority} | {due} |")
            md.append("")

        if transcript:
            md.append("## Full Verbatim Transcript\n")
            md.append("```text")
            md.append(transcript)
            md.append("```\n")

        return "\n".join(md)

    @staticmethod
    def to_txt(meeting_dict: Dict[str, Any]) -> str:
        title = meeting_dict.get("title", "Meeting Summary")
        created_at = meeting_dict.get("created_at", "")
        exec_summary = meeting_dict.get("executive_summary", "")
        decisions = meeting_dict.get("key_decisions", [])
        discussion_points = meeting_dict.get("discussion_points", [])
        action_items = meeting_dict.get("action_items", [])
        transcript = meeting_dict.get("transcript", "")

        lines = [
            f"MEETING SUMMARY: {title.upper()}",
            f"Generated: {created_at}",
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY:",
            exec_summary,
            "",
            "-" * 60,
            "KEY DECISIONS:",
        ]
        for d in decisions:
            lines.append(f"  * {d}")

        lines.extend(["", "-" * 60, "DISCUSSION POINTS:"])
        for p in discussion_points:
            lines.append(f"  * {p}")

        lines.extend(["", "-" * 60, "ACTION ITEMS:"])
        for item in action_items:
            status = "[DONE]" if item.get("status") == "completed" else "[TODO]"
            lines.append(f"  {status} {item.get('task')} (Assignee: {item.get('assignee')}, Priority: {item.get('priority')}, Due: {item.get('due_date')})")

        if transcript:
            lines.extend(["", "=" * 60, "TRANSCRIPT:", transcript])

        return "\n".join(lines)

    @staticmethod
    def to_json(meeting_dict: Dict[str, Any]) -> str:
        return json.dumps(meeting_dict, indent=2, default=str)

    @staticmethod
    def to_pdf_bytes(meeting_dict: Dict[str, Any]) -> bytes:
        """
        Generates a PDF using reportlab if available, or returns plain text encoded bytes.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#1E293B')
            )
            h2_style = ParagraphStyle(
                'DocHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#2563EB'),
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'DocBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#334155')
            )

            story = []
            title = meeting_dict.get("title", "Meeting Summary")
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 10))

            meta_text = f"<b>Date:</b> {meeting_dict.get('created_at', '')} | <b>Tone:</b> {meeting_dict.get('sentiment', 'Neutral')}"
            story.append(Paragraph(meta_text, body_style))
            story.append(Spacer(1, 15))

            # Executive summary
            story.append(Paragraph("Executive Summary", h2_style))
            story.append(Paragraph(meeting_dict.get("executive_summary", ""), body_style))
            story.append(Spacer(1, 10))

            # Decisions
            decisions = meeting_dict.get("key_decisions", [])
            if decisions:
                story.append(Paragraph("Key Decisions Made", h2_style))
                for d in decisions:
                    story.append(Paragraph(f"• {d}", body_style))
                story.append(Spacer(1, 10))

            # Action Items Table
            action_items = meeting_dict.get("action_items", [])
            if action_items:
                story.append(Paragraph("Action Items", h2_style))
                table_data = [["Status", "Task", "Assignee", "Priority", "Due Date"]]
                for item in action_items:
                    status = "Done" if item.get("status") == "completed" else "Pending"
                    table_data.append([
                        status,
                        item.get("task", ""),
                        item.get("assignee", "Unassigned"),
                        item.get("priority", "Medium"),
                        item.get("due_date", "TBD")
                    ])

                t = Table(table_data, colWidths=[50, 230, 85, 55, 60])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t)

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            # Fallback to plain text bytes
            txt = ExportService.to_txt(meeting_dict)
            return txt.encode("utf-8")

export_service = ExportService()
