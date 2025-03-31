import { jsPDF } from "jspdf";

class generatePdf {
  constructor(report) {
    this.report = report;
  }

  margin = 20;
  currentYPosition = 10;
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
    this.doc.text(text, this.margin, this.currentYPosition, {
      maxWidth: this.maxWidth,
    });
  }

  buildConclusions(conclusions) {
    conclusions.forEach(({ conclusion }, index) => {
      const { h: conclusionHeight } = this.doc.getTextDimensions(conclusion, {
        maxWidth: this.maxWidth,
      });

      const leading = index === 0 ? 10 : conclusionHeight;

      this.currentYPosition = this.currentYPosition + leading;

      this.setText(`• ${conclusion}`);
    });
  }

  buildQuestionsSection() {
    this.currentYPosition = 20;

    this.report.questions.forEach(({ name, conclusions }, index) => {
      const { h: questionHeight } = this.doc.getTextDimensions(name, {
        maxWidth: this.maxWidth,
      });

      const blockHeight = conclusions.reduce((totalHeight, conclusion) => {
        return (
          totalHeight +
          (this.doc.getTextDimensions(conclusion.conclusion, {
            maxWidth: this.maxWidth,
          }).h +
            10)
        );
      }, questionHeight);

      if (blockHeight + this.currentYPosition > this.maxHeight) {
        this.doc.addPage();
        this.doc.setPage(this.returnPageCount + 1);
        this.currentYPosition = 20;
      } else {
        this.currentYPosition = this.currentYPosition + questionHeight + 10;
      }

      this.doc.setFont("helvetica", "normal", "bold");
      this.doc.setFontSize(12);

      this.setText(`${index + 1}. ${name}`);

      this.currentYPosition = this.currentYPosition + questionHeight;

      this.doc.setFontSize(11);
      this.doc.setFont("helvetica", "normal", "regular");

      this.buildConclusions(conclusions);
    });
  }

  buildMetaSection() {
    this.currentYPosition = this.currentYPosition + 20;
    this.doc.setFont("helvetica", "normal", "bold");
    this.setText("Name: ");
    this.currentYPosition = this.currentYPosition + 10;
    this.doc.setFont("helvetica", "normal", "regular");
    this.setText(this.report.name);

    this.currentYPosition = this.currentYPosition + 20;
    this.doc.setFont("helvetica", "normal", "bold");
    this.setText("Analyst(s): ");
    this.currentYPosition = this.currentYPosition + 10;
    this.doc.setFont("helvetica", "normal", "regular");
    this.setText(this.report.analysts);

    this.currentYPosition = this.currentYPosition + 20;
    this.doc.setFont("helvetica", "normal", "bold");
    this.setText("Finalized Date & Time: ");
    this.currentYPosition = this.currentYPosition + 10;
    this.doc.setFont("helvetica", "normal", "regular");
    this.setText(this.report.finalizedTime.toISOString());

    this.currentYPosition = this.currentYPosition + 20;
    this.doc.setFont("helvetica", "normal", "bold");
    this.setText("Progress: ");
    this.currentYPosition = this.currentYPosition + 10;
    this.doc.setFont("helvetica", "normal", "regular");

    this.setText(
      `${this.report.completedQuestionsTotal}/${this.report.questionsTotal}`
    );

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

      this.doc.setFont("helvetica", "normal", "bold");
      this.setText("Report Summary: ");
      this.doc.setFont("helvetica", "normal", "regular");
      this.setText(this.report.summary[0].value);

      this.doc.addPage();
      this.doc.setPage(3);
    } else {
      this.currentYPosition = this.currentYPosition + 40;
      this.doc.setFont("helvetica", "normal", "bold");
      this.setText("Report Summary: ");
      this.currentYPosition = this.currentYPosition + 10;
      this.doc.setFont("helvetica", "normal", "regular");
      this.setText(this.report.summary[0].value);

      this.doc.addPage();
      this.doc.setPage(2);
    }
  }

  generatePdf() {
    this.doc.setFont("helvetica", "", "bold");
    this.doc.setFontSize(14);

    this.setText("Investigation Report");

    this.doc.setFontSize(11);
    this.doc.setFont("helvetica", "regular", "normal");

    this.buildMetaSection();
    this.buildQuestionsSection();

    this.doc.save(`dfiq-report-${this.report.id}.pdf`);
  }
}

export default generatePdf;
