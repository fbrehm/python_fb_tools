# For consistency and completeness
%global python2_pkgversion 2

%define version @@@Version@@@
%define builddir python_fb_tools-%{version}
%define builddir3 python38_fb_tools-%{version}

Name:		python38-fb-tools
Version:	%{version}
Release:	@@@Release@@@%{?dist}
Summary:	Python modules for common used objects, error classes and functions

Group:		Development/Languages/Python
License:	LGPL-3
Distribution:	Pixelpark
URL:		https://git.pixelpark.com/frabrehm/python_fb_tools
Source0:	https://git.pixelpark.com/frabrehm/python_fb_tools/repository/%{version}/fb_tools.%{version}.tar.gz

BuildRequires:	gettext
BuildRequires:	python38
BuildRequires:	python38-libs
BuildRequires:	python38-devel
BuildRequires:	python38-pytz
BuildRequires:	python38-setuptools
BuildRequires:	python38-babel
BuildRequires:	python38-six
Requires:	python38
Requires:	python38-libs
Requires:	python38-babel
Requires:	python38-requests
Requires:	python38-six
BuildArch:      noarch

%description
Python modules for common used objects, error classes and functions.

This is the Python38 version.

In this package are contained the following scripts:
 * get-file-to-remove
 * get-vmware-vm-info
 * get-vmware-vm-list
 * myip
 * pdns-bulk-remove
 * update-ddns

%prep
%setup -n %{builddir}
rm -rf ../%{builddir3}
cp -a . ../%{builddir3}

%build
cd ../%{builddir3}
python3.8 setup.py build

%install
cd ../%{builddir3}
echo "Buildroot: %{buildroot}"
python3.8 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%license debian/copyright
%doc README.md requirements.txt debian/changelog
%{_bindir}/get-file-to-remove
%{_bindir}/get-vmware-vm-info
%{_bindir}/get-vmware-vm-list
%{_bindir}/myip
%{_bindir}/pdns-bulk-remove
%{_bindir}/update-ddns
%{python3_sitelib}/*

%changelog
