[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
[![Website][website-shield]][website-url]


<!-- PROJECT LOGO -->

<div align="center">
  <a href="https://github.com/irvingmp6/kash">
    <img src="docs/images/readme-kash-logo.png" alt="Logo" width="300" height="auto">
  </a>
  <p align="center">
    An awesome personal finance framework!
    <br />
    <a href="https://irvingmp6.github.io/kash/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://irvingmp6.github.io/kash/Demo">View Demo</a>
    ·
    <a href="https://github.com/irvingmp6/kash/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/irvingmp6/kash/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>




<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

There are many great personal finance tools on the internet; however, I didn't find one that really suited my needs so I created this little project that I want to share with you.

Kash is a framework that allows you to better manage your financials. The framework consists of:
* A console app to consolidate and query your bank activity
* A pre-built Excel workbook template that contains all the ability to perform an accurate daily forecast of your financials for up to 3 months into the future

Here's why:
* We're human. We do human things like accidentally spend the money that was meant for the electric bill. 
* Your time is precious. We all know we should budget but no one has the time to scroll through their bank statements or to create complex formulas in an Excel spreadsheet.
* Unfortunately, a lot of personal finance tools fail to give you the financial insights that really tell you where you stand on a day-to-day basis.

This repository comes with all you need right out of the box. You just focus on the easy stuff.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

The console app was developed using Python 3.12. It uses *Pandas* and *SQLite* to do the heavy lifting.

* ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
* ![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
* ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

The pre-built workbook template was created using Excel.
* ![Microsoft Excel](https://img.shields.io/badge/Microsoft_Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white)

<p align="right">(<a href="#readme-top">back to top</a>)</p>





<!-- GETTING STARTED -->
## Getting Started

The installation process is fairly simple. There are just a couple prerequisites you want to make sure you have. 

### Prerequisites
* [Python 3.12](https://www.python.org/downloads/release/python-3123/)
* [Basic SQL knowledge](https://www.w3schools.com/sql/default.asp) (to set up your custom queries)

### Installation
Once you have Python 3.12 set up, you have the option of setting up a virtual environment.
#### (Optional) Setting up a Python Virtual Environment
To avoid updating current packages on your global python set up, it's always good practice to isolate any new package dependencies with a virtual environment.

**Create** a new Python virtual environment. I'm calling mine `kashEnv`.
```
$ python -v venv kashEnv
```
**Activate** the virtual environment (for Windows users)
```
$ source kashEnv/Scripts/activate 
```
**Activate** the virtual environment (for MacOS or Linux users)
```
$ source kashEnv/bin/activate
```
#### Installing the package
To install the package, follow tehese steps.

**Download** the repository
```
$ git clone git@github.com:irvingmp6/kash.git
```
Once you have the code downloaded, **install** Kash.
```
$ python -m pip install -e ./kash
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Add ability to consolidate bank activity into a single database
- [x] Add ability to fetch transactions from the console
- [ ] Add Changelog
- [ ] Add to documentation to the Kash Documentation Hub pages:
    - [ ] "Home"
    - [ ] "Getting Started"
    - [ ] "Importing Bank Transactions"
    - [ ] "Querying Bank Transactions"
    - [ ] "Forecasting"
    - [ ] "Tutorial"

See the [open issues](https://github.com/irvingmp6/kash/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Irving Martinez - [@irving-mtz](https://linkedin.com/in/irving-mtz) - irvingmp6@hotmail.com

Project Link: [https://github.com/irvingmp6/kash](https://github.com/irvingmp6/kash)

<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/irvingmp6/kash.svg?style=for-the-badge
[contributors-url]: https://github.com/irvingmp6/kash/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/irvingmp6/kash.svg?style=for-the-badge
[forks-url]: https://github.com/irvingmp6/kash/network/members
[stars-shield]: https://img.shields.io/github/stars/irvingmp6/kash.svg?style=for-the-badge
[stars-url]: https://github.com/irvingmp6/kash/stargazers
[issues-shield]: https://img.shields.io/github/issues/irvingmp6/kash.svg?style=for-the-badge
[issues-url]: https://github.com/irvingmp6/kash/issues
[license-shield]: https://img.shields.io/github/license/irvingmp6/kash.svg?style=for-the-badge
[license-url]: https://github.com/irvingmp6/kash/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/irving-mtz
[website-shield]: https://img.shields.io/badge/website-blue
[website-url]: https://img.shields.io/badge/any_text-you_like-blue
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
