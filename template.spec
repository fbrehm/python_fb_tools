%define version @@@Version@@@
%define builddir python@@@py_version_nodot@@@-fb-tools-%{version}

Name:           python@@@py_version_nodot@@@-fb-tools
Version:        %{version}
Release:        @@@Release@@@%{?dist}
Summary:        Python modules for common used objects, error classes and functions

Group:          Development/Languages/Python
License:        LGPL-3
Distribution:   Frank Brehm
URL:            https://github.com/fbrehm/python_fb_tools
Source0:        fb-tools.%{version}.tar.gz

BuildRequires:  gettext
BuildRequires:  python@@@py_version_nodot@@@
BuildRequires:  python@@@py_version_nodot@@@-libs
BuildRequires:  python@@@py_version_nodot@@@-devel
BuildRequires:  python@@@py_version_nodot@@@-setuptools
BuildRequires:  python@@@py_version_nodot@@@-babel
BuildRequires:  python@@@py_version_nodot@@@-pytz
BuildRequires:  python@@@py_version_nodot@@@-six
BuildRequires:  python@@@py_version_nodot@@@-fb-logging >= 1.0.0
BuildRequires:  python@@@py_version_nodot@@@-chardet
Requires:       python@@@py_version_nodot@@@
Requires:       python@@@py_version_nodot@@@-libs
Requires:       python@@@py_version_nodot@@@-babel
Requires:       python@@@py_version_nodot@@@-pytz
Requires:       python@@@py_version_nodot@@@-requests
Requires:       python@@@py_version_nodot@@@-six
Requires:       python@@@py_version_nodot@@@-fb-logging >= 1.0.0
Requires:       python@@@py_version_nodot@@@-chardet
Recommends:     python@@@py_version_nodot@@@-pyyaml
BuildArch:      noarch

%description
Python modules for common used objects, error classes and functions.

This is the Python@@@py_version_nodot@@@ version.

In this package are contained the following scripts:
 * get-file-to-remove
 * myip
 * update-ddns

%prep
echo "Preparing '${builddir}-' ..."
%setup -n %{builddir}

%build
cd ../%{builddir}
python@@@py_version_dot@@@ setup.py build

%install
cd ../%{builddir}
echo "Buildroot: %{buildroot}"
python@@@py_version_dot@@@ setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%license LICENSE
%doc LICENSE README.md requirements.txt debian/changelog
%{_bindir}/*
%{_datadir}/*
%{python3_sitelib}/*

%changelog

