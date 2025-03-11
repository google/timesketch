
const defaultTimeout = 5000
const defaultSnackBar = {
    "message": "",
    "color": "info",
    "timeout": defaultTimeout
}

// These methods will be available to all components without any further imports.
export const snackBarMixin = {
  methods: {
    successSnackBar(message) {
        let snackbar = defaultSnackBar
        snackbar.message = message
        snackbar.color = "success"
        console.log('success snack bar', message)
        this.appStore.setSnackBar(snackbar)
    },
    errorSnackBar(message) {
        let snackbar = defaultSnackBar
        snackbar.message = message
        snackbar.color = "error"
        this.appStore.setSnackBar(snackbar)
    },
    warningSnackBar(message) {
      let snackbar = defaultSnackBar
      snackbar.message = message
      snackbar.color = "warning"
      this.appStore.setSnackBar(snackbar)
    },
    infoSnackBar(message) {
      let snackbar = defaultSnackBar
      snackbar.message = message
      snackbar.color = "info"
      snackbar.timeout = 2000
      this.appStore.setSnackBar(snackbar)
    },
  }
}
