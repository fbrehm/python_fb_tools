%define version @@@Version@@@
%define builddir %{_builddir}/python%{python3_pkgversion}-fb-tools-%{version}

Name:           python%{python3_pkgversion}-fb-tools
Version:        %{version}
Release:        @@@Release@@@%{?dist}
Summary:        Python modules for common used objects, error classes and functions

Group:          Development/Languages/Python
License:        LGPL-3
Distribution:   Frank Brehm
URL:            https://github.com/fbrehm/python_fb_tools
Source0:        fb-tools.%{version}.tar.gz

BuildRequires:  gettext
BuildRequires:  python%{python3_pkgversion}
BuildRequires:  python%{python3_pkgversion}-libs
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-babel
BuildRequires:  python%{python3_pkgversion}-pytz
BuildRequires:  python%{python3_pkgversion}-six
BuildRequires:  python%{python3_pkgversion}-fb-logging >= 1.0.0
BuildRequires:  python%{python3_pkgversion}-chardet
BuildRequires:  python%{python3_pkgversion}-pyyaml
BuildRequires:  pyproject-rpm-macros
Requires:       python%{python3_pkgversion}
Requires:       python%{python3_pkgversion}-libs
Requires:       python%{python3_pkgversion}-babel
Requires:       python%{python3_pkgversion}-pytz
Requires:       python%{python3_pkgversion}-requests
Requires:       python%{python3_pkgversion}-six
Requires:       python%{python3_pkgversion}-fb-logging >= 1.0.0
Requires:       python%{python3_pkgversion}-chardet
Requires:       python%{python3_pkgversion}-pyyaml
Requires:       python%{python3_pkgversion}-semver
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
echo "Pwd: $( pwd )"
%autosetup -p1 -v

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files fb_tools

echo "Whats in '%{builddir}':"
ls -lA '%{builddir}'

echo "Whats in '%{buildroot}':"
ls -lA '%{buildroot}'

%files -f %{pyproject_files}
%defattr(-,root,root,-)
%license LICENSE
%doc LICENSE README.md pyproject.toml debian/changelog
%{_bindir}/*
%{_mandir}/*

%changelog
