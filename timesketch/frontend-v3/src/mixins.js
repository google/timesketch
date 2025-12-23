const defaultTimeout = 5000

// These methods will be available to all components without any further imports.
export const snackBarMixin = {
  methods: {
    successSnackBar(message, timeout = defaultTimeout) {
        const snackbar = {
            message: message,
            color: "success",
            timeout: timeout
        }
        console.log('success snack bar', message)
        this.appStore.setSnackBar(snackbar)
    },
    errorSnackBar(message, timeout = defaultTimeout) {
        const snackbar = {
            message: message,
            color: "error",
            timeout: timeout
        }
        this.appStore.setSnackBar(snackbar)
    },
    warningSnackBar(message, timeout = defaultTimeout) {
        const snackbar = {
            message: message,
            color: "warning",
            timeout: timeout
        }
        this.appStore.setSnackBar(snackbar)
    },
    infoSnackBar(message, timeout = 2000) {
        const snackbar = {
            message: message,
            color: "info",
            timeout: timeout
        }
        this.appStore.setSnackBar(snackbar)
    },
  }
}
