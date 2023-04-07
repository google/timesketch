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
Compute the redis url if not set explicitly.
*/}}
{{- define "timesketch.configmap.name" -}}
{{- printf "redis://%s-master:%.0f" (include "timesketch.redis.fullname" .) .Values.redis.master.service.ports.redis -}}
{{- end -}}

{{/*
Redis subcharts fullname
*/}}
{{- define "timesketch.redis.fullname" -}}
{{- if .Values.redis.enabled -}}
{{- include "common.names.fullname" (dict "Chart" (dict "Name" "redis") "Release" .Release "Values" .Values.redis) -}}
{{- else -}}
{{ fail "attempting to use redis subcharts fullname, even though the subchart is not enabled. This will lead to misconfiguration" }}
{{- end -}}
{{- end -}}

{{/*
Compute the redis url if not set explicitly.
*/}}
{{- define "timesketch.redis.ConnectionUrl" -}}
{{- if .Values.redis.enabled -}}
{{- printf "redis://%s-master:%.0f" (include "timesketch.redis.fullname" .) .Values.redis.master.service.ports.redis -}}
{{- else -}}
{{ fail "please set sessionStorage.redis.standalone.connectionUrl or enable the redis subchart via redis.enabled" }}
{{- end -}}
{{- end -}}