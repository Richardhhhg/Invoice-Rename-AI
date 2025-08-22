<h1 align="center">Invoice Rename AI</h1>
<p align="center">A free and open source tool for renaming invoices according to it's contents</p>

## Summary
Utilizing LLM models, the goal of this project is to save labour hours for people working in finance related jobs by automatically renaming invoices that are uploaded.
  
Currently this app only supports renaming in the format companyName_invoiceNumber_invoiceTotal_date.extension but is planned to support more customizability.

> [!NOTE]
>
> This project is still in very early stages of development. We are looking for anyone interested to also join in.
> For more information see [contributing](#contributing)
> 

## Development Progress
### Minimum Viable Product
- [x] Backend AI that reads and renames invoice file
- [x] Frontend website (This is currently all coded by claude)
    - [x] Giving users place to upload invoices (should support any image type + pdf)
    - [x] Button for processing and downloading invoices

### TODO / Upgrades
- [ ] Actually deploy to web
- [ ] Rewrite lots of frontend code to be more organized
- [ ] Giving Users ability to customize how they want their invoice renamed
- [ ] More robust cleaning after extracting key data from invoice (potentially using some sort of LLM model)
- [ ] Loading models before user clicks download button

## Compatibility
python: This should work for python 3.9 or 3.10 due to docquery. Built using 3.10.18

## How to Run
1. Install Requirements.txt
2. Run app.py

## Contributing
### Templates
There are currently no templates for pull requests and issues, but this may change depending on the furue scale of the project.
  
### Contributor Applications
If you would like to be added as a contributor to this repository, introduce yourself in the discussions tab under general. Please list any relevant skills and interests.

### Feature Requests
For new features, please create an issue with the proposed feature and the `New Feature` label. Ideally, be as specific as you can. 

### Bugs
For any observed bugs, please create an issue reporting:
1. What is the bug
2. If you can, how to reproduce the bug
  
Lastly, please add the label `Bug` to the issue.

### Pull Requests
This repository is open for pull requests. In the pull request, please state a short non technical summary of the changes followed by a more technical description of changes.