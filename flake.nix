{
  description = "Nix flake packaging for geodepot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          lib = pkgs.lib;
          python = pkgs.python312;
          pyPkgs = python.pkgs;

          pdalPython = pyPkgs.buildPythonPackage rec {
            pname = "pdal";
            version = "3.4.5";
            pyproject = true;

            src = pkgs.fetchFromGitHub {
              owner = "PDAL";
              repo = "python";
              rev = version;
              hash = "sha256-bOiXgERlf0u7Vdsex9cQgeKzHP5y6qeBCGvpI7sbZ30=";
            };

            nativeBuildInputs = [
              pyPkgs.cmake
              pyPkgs.ninja
              pyPkgs.scikit-build-core
              pyPkgs.pybind11
              pkgs.cmake
              pkgs.ninja
              pkgs.pkg-config
            ];

            buildInputs = [
              pkgs.pdal
            ];

            propagatedBuildInputs = [
              pyPkgs.numpy
            ];

            postPatch = ''
              substituteInPlace pyproject.toml \
                --replace-fail '"pybind11[global]"' '"pybind11"'
            '';

            dontUseCmakeConfigure = true;
            doCheck = false;
            pythonImportsCheck = [ "pdal" ];
          };

          geodepot = pyPkgs.buildPythonApplication rec {
            pname = "geodepot";
            version = "1.0.8";
            pyproject = true;
            src = ./.;

            nativeBuildInputs = [
              pyPkgs.hatchling
              pkgs.makeWrapper
            ];

            buildInputs = [
              pkgs.gdal
              pkgs.pdal
              pkgs.proj
            ];

            propagatedBuildInputs = [
              pyPkgs.click
              pyPkgs.fabric
              pyPkgs.gdal
              pdalPython
              pyPkgs.requests
            ];

            pythonRelaxDeps = [
              "click"
              "fabric"
              "gdal"
              "pdal"
              "requests"
            ];

            doCheck = false;
            pythonImportsCheck = [ "geodepot" ];

            postFixup = ''
              wrapProgram "$out/bin/geodepot" \
                --prefix PATH : "${lib.makeBinPath [ pkgs.gdal pkgs.pdal ]}" \
                --set GDAL_DATA "${pkgs.gdal}/share/gdal" \
                --set GDAL_DRIVER_PATH "${pkgs.gdal}/lib/gdalplugins" \
                --set PROJ_DATA "${pkgs.proj}/share/proj" \
                --set PDAL_DRIVER_PATH "$out/${python.sitePackages}/pdal:${pkgs.pdal}/lib" \
                --set CPL_ZIP_ENCODING "UTF-8"
            '';

            meta = {
              description = "Test data storage system for geospatial data";
              homepage = "https://github.com/3DBAG/geodepot";
              license = lib.licenses.asl20;
              mainProgram = "geodepot";
            };
          };
        in
        {
          default = geodepot;
          geodepot = geodepot;
          pdal-python = pdalPython;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/geodepot";
        };
      });
    };
}
