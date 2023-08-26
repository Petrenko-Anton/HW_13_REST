# Minimal makefile for Sphinx documentation
#

export POSTGRES_DB=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=567234
export POSTGRES_PORT=5432
export POSTGRES_URL=localhost

export SQLALCHEMY_DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_URL}:${POSTGRES_PORT}/${POSTGRES_DB}

export SECRET_KEY=secret_key
export ALGORITHM=HS256


export MAIL_USERNAME=email-robot@meta.ua
export MAIL_PASSWORD=Robot_159357!
export MAIL_FROM=email-robot@meta.ua
export MAIL_PORT=465
export MAIL_SERVER=smtp.meta.ua
export MAIL_FROM_NAME=Email-robot

export REDIS_HOST=localhost
export REDIS_PORT=6379

export CLOUDINARY_NAME=diqj3bfmh
export CLOUDINARY_API_KEY=892455627639111
export CLOUDINARY_API_SECRET=NIgg-YWDDW3cHAoH571b-GoOg-M

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
