{{/*
Expand the name of the chart.
*/}}
{{- define "timesketch.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "timesketch.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "timesketch.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "timesketch.labels" -}}
helm.sh/chart: {{ include "timesketch.chart" . }}
{{ include "timesketch.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "timesketch.selectorLabels" -}}
app.kubernetes.io/name: {{ include "timesketch.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "timesketch.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "timesketch.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Redis subcharts connection url
*/}}
{{- define "timesketch.redis.url" -}}
{{- if .Values.redis.enabled -}}
{{- $name := include "common.names.fullname" (dict "Chart" (dict "Name" "redis") "Release" .Release "Values" .Values.redis) -}}
{{- $port := .Values.redis.master.service.ports.redis -}}
{{- if .Values.redis.auth.enabled -}}
{{- printf "redis://default:'$REDIS_PASSWORD'@%s-master:%.0f" $name $port -}}
{{- else -}}
{{- printf "redis://%s-master:%.0f" $name $port -}}
{{- end -}}
{{- else -}}
{{ fail "Attempting to use Redis, but the subchart is not enabled. This will lead to misconfiguration" }}
{{- end -}}
{{- end -}}

{{/*
Postgresql subcharts connection url
*/}}
{{- define "timesketch.postgresql.url" -}}
{{- if .Values.postgresql.enabled -}}
{{- $name := include "common.names.fullname" (dict "Chart" (dict "Name" "postgresql") "Release" .Release "Values" .Values.postgresql) -}}
{{- $port := .Values.postgresql.primary.service.ports.postgresql -}}
{{- $username := .Values.postgresql.auth.username -}}
{{- $database := .Values.postgresql.auth.database -}}
{{- printf "postgresql://%s:'$POSTGRES_PASSWORD'@%s:%.0f/%s" $username $name $port $database -}}
{{- else -}}
{{ fail "Attempting to use Postgresql, but the subchart is not enabled. This will lead to misconfiguration" }}
{{- end -}}
{{- end -}}

{{/*
Opensearch subcharts host name
*/}}
{{- define "timesketch.opensearch.host" -}}
{{- if .Values.opensearch.enabled -}}
{{- printf "%s" .Values.opensearch.masterService -}}
{{- else -}}
{{ fail "Attempting to use Opensearch, but the subchart is not enabled. This will lead to misconfiguration" }}
{{- end -}}
{{- end -}}

{{/*
Opensearch subcharts port
*/}}
{{- define "timesketch.opensearch.port" -}}
{{- if .Values.opensearch.enabled -}}
{{- printf "%.0f" .Values.opensearch.httpPort -}}
{{- else -}}
{{ fail "Attempting to use Opensearch, but the subchart is not enabled. This will lead to misconfiguration" }}
{{- end -}}
{{- end -}}