%{!?python3_version_nodots:%global python3_version_nodots 3}

# For consistency and completeness
%global python2_pkgversion 2

%define version @@@Version@@@
%define builddir2 python_fb_tools-%{version}
%define builddir3 python%{python3_version_nodots}_fb_tools-%{version}

Name:		python%{python3_version_nodots}-fb-tools
Version:	%{version}
Release:	@@@Release@@@%{?dist}
Summary:	Python modules for common used objects, error classes and functions

Group:		Development/Languages/Python
License:	LGPL-3
Distribution:	Pixelpark
URL:		https://git.pixelpark.com/frabrehm/python_fb_tools
Source0:	https://git.pixelpark.com/frabrehm/python_fb_tools/repository/%{version}/fb_tools.%{version}.tar.gz

BuildRequires:	gettext
BuildRequires:	python%{python3_version_nodots}
BuildRequires:	python%{python3_version_nodots}-libs
BuildRequires:	python%{python3_version_nodots}-devel
BuildRequires:	python%{python3_version_nodots}-pytz
BuildRequires:	python%{python3_version_nodots}-setuptools
BuildRequires:	python%{python3_version_nodots}-babel
BuildRequires:	python%{python3_version_nodots}-six
Requires:	python%{python3_version_nodots}
Requires:	python%{python3_version_nodots}-libs
Requires:	python%{python3_version_nodots}-babel
Requires:	python%{python3_version_nodots}-requests
Requires:	python%{python3_version_nodots}-six
BuildArch:      noarch

%description
Python modules for common used objects, error classes and functions.

This is the Python%{python3_version_nodots} version.

In this package are contained the following scripts:
 * get-file-to-remove
 * get-vmware-vm-info
 * get-vmware-vm-list
 * myip
 * update-ddns

%prep
%setup -n %{builddir2}
rm -rf ../%{builddir3}
cp -a . ../%{builddir3}

%build
cd ../%{builddir3}
python3 setup.py build

%install
cd ../%{builddir3}
echo "Buildroot: %{buildroot}"
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%license debian/copyright
%doc README.md requirements.txt debian/changelog
%{_bindir}/get-file-to-remove
%{_bindir}/get-vmware-vm-info
%{_bindir}/get-vmware-vm-list
%{_bindir}/myip
%{_bindir}/update-ddns
%{python3_sitelib}/*

%changelog
