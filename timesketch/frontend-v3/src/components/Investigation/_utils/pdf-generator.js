import { jsPDF } from "jspdf";

class generatePdf {
  constructor(report) {
    this.conclusionSummaries = report.conclusionSummaries || []
    this.report = report;
  }

  margin = 20;
  currentYPosition = 20;
  doc = new jsPDF({
    unit: "px",
    compressPdf: true,
  });

  get maxHeight() {
    return this.doc.internal.pageSize.getHeight() - this.margin * 2;
  }

  get maxWidth() {
    return this.doc.internal.pageSize.getWidth() - this.margin * 2;
  }

  get returnPageCount() {
    return this.doc.internal.pages.length;
  }

  setText(text) {
    this.doc.text(text || '', this.margin, this.currentYPosition, {
      maxWidth: this.maxWidth,
    });
  }

  buildQuestionsSection() {
    this.report.questions.forEach((question, index) => {
      // Calculate heights first for page break logic
      const questionText = `${index + 1}. ${question.name}`
      const { h: questionHeight } = this.doc.getTextDimensions(questionText, { maxWidth: this.maxWidth })

      const answerSummary = this.conclusionSummaries.find((s) => s.questionId === question.id)
      const answerText = answerSummary ? answerSummary.value : 'No answer provided.'
      const { h: answerHeight } = this.doc.getTextDimensions(answerText, { maxWidth: this.maxWidth })

      // 10 for space between Q/A, 20 for space after answer before next question
      const blockHeight = questionHeight + 10 + answerHeight + 20

      if (this.currentYPosition + blockHeight > this.maxHeight) {
        this.doc.addPage()
        this.currentYPosition = this.margin
      }

      // Render Question
      this.doc.setFontSize(12)
      this.doc.setFont('helvetica', 'bold')
      this.setText(questionText)
      this.currentYPosition += questionHeight

      // Render Answer
      this.currentYPosition += 10 // space
      this.doc.setFontSize(11)
      this.doc.setFont('helvetica', 'normal')
      this.setText(answerText)
      this.currentYPosition += answerHeight

      // Space after the whole block
      this.currentYPosition += 20
    });
  }

  buildMetaSection() {
    [
      {
        label: "Name:",
        value: this.report.name,
      },
      {
        label: "Analyst(s):",
        value: this.report.analysts,
      },
      {
        label: "Finalized Date & Time:",
        value: this.report.finalizedTime.format("YYYY-MM-DD HH:mm"),
      },
      {
        label: "Progress:",
        value: `${this.report.completedQuestionsTotal}/${this.report.questionsTotal} questions completed`,
      },
    ].forEach(({ value, label }) => {
      this.currentYPosition = this.currentYPosition + 20;
      this.doc.setFont('helvetica', 'bold');
      this.setText(label);
      this.currentYPosition = this.currentYPosition + 10;
      this.doc.setFont('helvetica', 'normal');
      this.setText(value);
    });

    const { h: summaryHeight } = this.doc.getTextDimensions(
      this.report.summary[0].value,
      {
        maxWidth: this.maxWidth,
      }
    );

    if (summaryHeight + this.currentYPosition > this.maxHeight) {
      this.currentYPosition = 20;

      this.doc.addPage();
      this.doc.setPage(2);

      this.doc.setFont('helvetica', 'bold');
      this.setText("Report Summary: ");
      this.doc.setFont('helvetica', 'normal');
      this.setText(this.report.summary?.[0]?.value || 'No summary provided.');

      this.doc.addPage();
      this.doc.setPage(3);
    } else {
      this.currentYPosition = this.currentYPosition + 40;
      this.doc.setFont('helvetica', 'bold');
      this.setText("Report Summary: ");
      this.currentYPosition = this.currentYPosition + 10;
      this.doc.setFont('helvetica', 'normal');
      this.setText(this.report.summary[0].value);

      this.doc.addPage();
      this.doc.setPage(2);
    }

    this.currentYPosition = 20;
  }

  generatePdf() {
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(14);

    this.setText("Investigation Report");

    this.doc.setFontSize(11)
    this.doc.setFont('helvetica', 'normal')

    this.buildMetaSection();
    this.buildQuestionsSection();

    this.doc.save(`investigation-report-sketch-${this.report.id}.pdf`);
  }
}

export default generatePdf;
