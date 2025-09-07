class CliTyper < Formula
  include Language::Python::Virtualenv

  desc "Curses-based terminal typing practice tool"
  homepage "https://github.com/AmudanThangavel/cli-typer"
  url "https://github.com/AmudanThangavel/cli-typer/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"cli-typer", "--check"
  end
end
