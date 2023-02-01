# Authomize-ITDR
 Authomize open solutions for partners and customers
# Video Demonstration
Check out the following video on YouTube for a project overview and demonstration of Falcon Orchestrator.

# Support
As an open source project this software is not officially supported by CrowdStrike. As such we ask that you please refrain from sending inquiries to the CrowdStrike support team. The project maintainers will be working with active community contributors to address bugs and supply new features. If you have identified a bug please submit an issue through GitHub by following the contribution guidelines. You can also post questions or start conversations on the project through our community forums page.

# You can also join the project chat room to discuss in greater detail, click Slack to sign up. Please note that the email you sign up with will be viewable by other users. If you wish to keep your company name anonymous you should use a personal email that holds no affiliation.

# Getting Started
Please refer to the Wiki page for instructions on installing and configuring the application. You can download the installer through the release page.

# Development
Being a Windows based application, the tool was developed with the use of .NET 4.5, C#, ASP.NET MVC 4, Entity Framework and PowerShell. If forking or cloning the repository, please note the code was written with Visual Studio 2015. Compatibility with earlier Visual Studio versions can be problematic. You can either rebuild projects individually and copy over the compiled DLL/EXE to the requires location or alternatively re-complile the installer project to produce a new MSI package with you code changes. To do this, open a visual studio command prompt, change directories to the FalconOrchestrator.Installer project and execute the command msbuild /t:Build;PublishWebSite;Harvest;WIX setup.build

# Third Party Libraries
The following external libraries are used within the project. These are not provided via the GitHub repository, if building from source you will need to right click on the solution file in Visual Studio and select Restore NuGet Packages.
