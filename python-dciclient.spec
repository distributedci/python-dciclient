%if 0%{?fedora}
%global with_python3 1
%endif

Name:           python-dciclient
Version:        0.0.VERS
Release:        1%{?dist}

Summary:        Python client for DCI control server
License:        ASL 2.0
URL:            https://github.com/redhat-cip/python-dciclient

Source0:        dciclient-%{version}.tar.gz

BuildArch:      noarch

%description
Python client for DCI control server for the remote CIs.

%package -n python2-dciclient
Summary:        Python client for DCI control server
%{?python_provide:%python_provide python2-dciclient}
BuildRequires:  PyYAML
BuildRequires:  dci-api
BuildRequires:  postgresql
BuildRequires:  postgresql-devel
BuildRequires:  postgresql-server
BuildRequires:  python-click
BuildRequires:  python2-pifpaf
BuildRequires:  python-mock
BuildRequires:  python-prettytable
BuildRequires:  python-psycopg2
BuildRequires:  python-pytest
BuildRequires:  python-requests
BuildRequires:  python-rpm-macros
BuildRequires:  python-six
BuildRequires:  python-tox
BuildRequires:  python2-setuptools
BuildRequires:  python2-rpm-macros
BuildRequires:  python3-rpm-macros
Requires:       PyYAML
Requires:       py-bcrypt
Requires:       python-click
Requires:       python-configparser
Requires:       python-prettytable
Requires:       python-requests
Requires:       python-simplejson
Requires:       python-six
Requires:       python2-setuptools

%description -n python2-dciclient
A Python 2 implementation of the client for DCI control server.

%if 0%{?with_python3}
%package -n python3-dciclient
Summary:        Python client for DCI control server
%{?python_provide:%python_provide python3-dciclient}

BuildRequires:  postgresql
BuildRequires:  postgresql-server
BuildRequires:  python-tox
BuildRequires:  python3-PyYAML
BuildRequires:  python3-click
BuildRequires:  python3-prettytable
BuildRequires:  python3-psycopg2
BuildRequires:  python3-requests
BuildRequires:  python3-setuptools
BuildRequires:  python3-six
Requires:       python3-PyYAML
Requires:       python3-click
Requires:       python3-prettytable
Requires:       python3-py-bcrypt
Requires:       python3-requests
Requires:       python3-simplejson
Requires:       python3-six


%description -n python3-dciclient
A Python 3 implementation of the client for DCI control server.
%endif

%prep
%autosetup -n dciclient-%{version}

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif

%install
install -d %{buildroot}%{_bindir}
%py2_install
%if 0%{?with_python3}
%py3_install
%endif

%check
PYTHONPATH=%{buildroot}%{python2_sitelib} \
          DCI_SETTINGS_MODULE="dciclient.v1.tests.settings" \
          pifpaf run postgresql -- py.test -v dciclient

%files -n python2-dciclient
%doc
%{python2_sitelib}/*
%{_bindir}/dcictl

%if 0%{?with_python3}
%files -n python3-dciclient
%doc
%{python3_sitelib}/*
%{_bindir}/dcictl
%endif


%changelog
* Tue Mar 08 2016 Brad Watkins <bwatkins@redhat.com> - 0.1-1
- Add dci-feeder-github sysconfig directory

* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
