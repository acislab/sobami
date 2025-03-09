# iChatBio Weekly Summary

The service picks the list of recipients from `home/nitingoyal/crons/ichatbio-weekly/recipients.json` file. There is no need to reload the service if this file has been altered, newly added participants will receive emails in the next run.

## Monitoring

These are some helpful commands to debug the service quickly. The service make use of it's virtual environment to resolve dependencies.

```bash
# Check service timer enabled or not
sudo systemctl list-timers

# Check service status
sudo systemctl status ichatbio-weekly.service

# Check service logs
sudo journalctl -u ichatbio-weekly.service -n 50

# Check python script logs
sudo tail -n 50 /var/log/weekly-email.log

# Run service manually
source /home/nitingoyal/ichatbio-weekly/venv/bin/activate
python /home/nitingoyal/ichatbio-weekly/main.py
```
