## Usage

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to
Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

  helm repo add timesketch https://timesketch-charts.storage.googleapis.com

If you had already added this repo earlier, run `helm repo update` to retrieve
the latest versions of the packages.  You can then run `helm search repo
timesketch` to see the charts.

To install the Timesketch chart:

  helm install my-timesketch timesketch/timesketch --wait

To pull the Timesketch chart locally:

  helm pull timesketch --repo https://timesketch-charts.storage.googleapis.com

To install the Timesketch chart from a local repo:

  helm install my-timesketch timesketch/ --wait

To uninstall the chart:

  helm delete my-timesketch