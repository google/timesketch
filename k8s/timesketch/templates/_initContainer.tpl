{{/*
Init Container for when a Timesketch pod starts. To prevent duplicate code,
this file has been created which then applies to both the Timesketch Web and
Worker pod upon startup.
*/}}
{{- define "timesketch.initContainer" -}}
{{- $globconfigs := .Files.Glob "configs/*" -}}
- name: init-timesketch
  image: busybox
  command: ['sh', '-c', '/init/init-timesketch.sh']
  env:
    - name: TIMESKETCH_SECRET
      valueFrom:
        secretKeyRef:
          name: {{ include "timesketch.fullname" . }}-secret 
          key: timesketch-secret
    {{- if and .Values.redis.enabled .Values.redis.auth.enabled }}
    - name: REDIS_PASSWORD
      valueFrom:
        # Referencing from charts/redis/templates/_helpers.tpl
        secretKeyRef:
          name: {{ include "redis.secretName" .Subcharts.redis }}
          key: {{ include "redis.secretPasswordKey" .Subcharts.redis }}
    {{- end }}
    {{- if .Values.postgresql.enabled }}
    - name: POSTGRES_PASSWORD
      valueFrom:
        # Referencing from charts/postgresql/templates/_helpers.tpl
        secretKeyRef:
          name: {{ include "postgresql.secretName" .Subcharts.postgresql }}
          key: {{ include "postgresql.adminPasswordKey" .Subcharts.postgresql }}
    {{- end }}
  volumeMounts:
    - mountPath: /init
      name: init-timesketch
    - mountPath: /etc/timesketch
      name: timesketch-configs
    {{- if $globconfigs }}
    - mountPath: /tmp/timesketch
      name: uploaded-configs
    {{- end }}
{{- end }}
