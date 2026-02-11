FROM us-docker.pkg.dev/osdfir-registry/picatrix/picatrix:latest

USER picatrix

ENV VIRTUAL_ENV="/home/picatrix/picenv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
ENV JUPYTER_PORT="8844"

RUN mkdir -p \
    "/home/picatrix/.local/share/jupyter/nbextensions/snippets/" \
    "/home/picatrix/.jupyter/custom"

COPY --chown=1000:1000 ["contrib/docker/dev/notebook/timesketchrc", "/home/picatrix/.timesketchrc"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/timesketch_token", "/home/picatrix/.timesketch.token"]
COPY --chown=1000:1000 [".", "/home/picatrix/code"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/snippets.json", "/home/picatrix/.local/share/jupyter/nbextensions/snippets/snippets.json"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/10-widgets.py", "/home/picatrix/.ipython/profile_default/startup/10-widgets.py"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/logo.png", "/home/picatrix/.jupyter/custom/logo.png"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/custom.css", "/home/picatrix/.jupyter/custom/custom.css"]
COPY --chown=1000:1000 ["contrib/docker/dev/notebook/timesketch", "/home/picatrix/picenv/share/jupyter/nbextensions/timesketch"]

ARG PYTHON_PIP_CONF=""
RUN if [ -n "${PYTHON_PIP_CONF}" ]; then \
    mkdir -p ~/.config/pip; \
    env echo -e "${PYTHON_PIP_CONF}" > ~/.config/pip/pip.conf; \
  fi

RUN sed -i -e "s/c.NotebookApp.token = 'picatrix'/c.NotebookApp.token = 'timesketch'/g" /home/picatrix/.jupyter/jupyter_notebook_config.py \
    && sed -i -e "s/c.NotebookApp.port = 8899/c.NotebookApp.port = ${JUPYTER_PORT}/g" /home/picatrix/.jupyter/jupyter_notebook_config.py \
    && pip install -e /home/picatrix/code/api_client/python \
    && pip install -e /home/picatrix/code/importer_client/python/ \
    && jupyter nbextension enable snippets/main \
    && jupyter nbextension enable timesketch/main \
    && pip install ipydatetime \
    && jupyter nbextension install --user --py ipydatetime \
    && jupyter nbextension enable --user --py ipydatetime

WORKDIR /usr/local/src/picadata
EXPOSE 8844

# Run jupyter.
ENTRYPOINT ["jupyter", "notebook"]
