@echo off
echo === GIT SETUP DEBUG LOG === > git_setup_log.txt
echo Current directory: %CD% >> git_setup_log.txt

echo. >> git_setup_log.txt
echo === CHECKING GIT VERSION === >> git_setup_log.txt
git --version >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === CHECKING GIT DIRECTORY === >> git_setup_log.txt
dir .git /a >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === REMOVING OLD .GIT IF EXISTS === >> git_setup_log.txt
if exist .git (
  rmdir /s /q .git
  echo .git directory removed >> git_setup_log.txt
) else (
  echo No .git directory found >> git_setup_log.txt
)

echo. >> git_setup_log.txt
echo === INITIALIZING REPOSITORY === >> git_setup_log.txt
git init >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === SETTING USER NAME AND EMAIL === >> git_setup_log.txt
git config user.name "HolyWill90" >> git_setup_log.txt 2>&1
git config user.email "william.watfeh@gmail.com" >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === ADDING REMOTE === >> git_setup_log.txt
git remote add origin https://github.com/HolyWill90/DataProcessor.git >> git_setup_log.txt 2>&1
git remote -v >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === STAGING FILES === >> git_setup_log.txt
git add . >> git_setup_log.txt 2>&1
git status >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === MAKING INITIAL COMMIT === >> git_setup_log.txt
git commit -m "Initial commit" >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === CHECKING COMMIT HISTORY === >> git_setup_log.txt
git log >> git_setup_log.txt 2>&1

echo. >> git_setup_log.txt
echo === SETUP COMPLETE === >> git_setup_log.txt
echo To push to GitHub, run: git push -u origin main >> git_setup_log.txt

echo Git setup complete. Check git_setup_log.txt for details.