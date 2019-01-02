# Single python3 version in Fedora, python3_pkgversion macro not available
%{!?python3_pkgversion:%global python3_pkgversion 3}

# For consistency and completeness
%global python2_pkgversion 2

%define version 1.3.7
%define builddir2 python_fb_tools-%{version}
%define builddir3 python%{python3_pkgversion}_fb_tools-%{version}

Name:		python-fb-tools
Version:	%{version}
Release:	1%{?dist}
Summary:	Python modules for common used objects, error classes and functions

Group:		Development/Languages/Python
License:	LGPL-3
Distribution:	Pixelpark
URL:		https://git.pixelpark.com/frabrehm/python_fb_tools
Source0:	https://git.pixelpark.com/frabrehm/python_fb_tools/repository/%{version}/fb_tools.%{version}.tar.gz

BuildRequires:	gettext
BuildRequires:	python
BuildRequires:	python-libs
BuildRequires:	python-devel
BuildRequires:	python-setuptools
BuildRequires:	python-pathlib
BuildRequires:	python-babel
BuildRequires:	python-ipaddress
BuildRequires:	pytz
BuildRequires:	python%{python3_pkgversion}
BuildRequires:	python%{python3_pkgversion}-libs
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-pytz
BuildRequires:	python%{python3_pkgversion}-setuptools
BuildRequires:	python%{python3_pkgversion}-babel
Requires:	python
Requires:	python-libs
Requires:	python-babel
Requires:	python-pathlib
Requires:	python-ipaddress


%description
Python modules for common used objects, error classes and functions.

This is the Python2 version.

%package -n     python%{python3_pkgversion}-fb-tools
Summary:	Python modules for common used objects, error classes and functions
Requires:	python%{python3_pkgversion}
Requires:	python%{python3_pkgversion}-libs
Requires:	python%{python3_pkgversion}-babel

%description -n     python%{python3_pkgversion}-fb-tools
Python modules for common used objects, error classes and functions.

This is the Python%{python3_pkgversion} version.

In this package are contained the following scripts:
 * get-file-to-remove
 * get-vmware-vm-info
 * pdns-bulk-remove

%prep
%setup -n %{builddir2}
rm -rf ../%{builddir3}
cp -a . ../%{builddir3}


%build
cd ../%{builddir2}
python2 setup.py build
#pushd ../%{builddir3}
cd ../%{builddir3}
python3 setup.py build
#popd
cd ../%{builddir2}

%install
cd ../%{builddir2}
#pushd ../%{builddir2}
echo "Buildroot: %{buildroot}"
python2 setup.py install --prefix=%{_prefix} --root=%{buildroot}
rm -rv %{buildroot}/%{_bindir}
#popd
cd ../%{builddir3}
echo "Buildroot: %{buildroot}"
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%{python2_sitelib}/*

%files -n python%{python3_pkgversion}-fb-tools
%defattr(-,root,root,-)
%{_bindir}/get-file-to-remove
%{_bindir}/get-vmware-vm-info
%{_bindir}/pdns-bulk-remove
%{python3_sitelib}/*

%changelog
*   Wed Jan 02 2019 Frank Brehm <frank.brehm@pixelpark.com> 1.3.7-1
-   Version bump to 1.3.7
*   Wed Jan 02 2019 Frank Brehm <frank.brehm@pixelpark.com> 1.3.6-1
-   Initial

